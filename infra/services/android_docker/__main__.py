# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
from datetime import datetime
import fcntl
import logging
import logging.handlers
import os
import socket
import subprocess
import sys
import time

from infra.services.android_docker import containers
from infra.services.android_docker import usb_device


_REGISTRY_URL = 'gcr.io'


def reboot_devices(devices, path_to_adb):
  try:
    subprocess.check_call([path_to_adb, 'start-server'])
  except subprocess.CalledProcessError:
    logging.exception('Unable to start adb server.')
    return
  try:
    for device in devices:
      serial = device.serial
      if not serial:
        logging.warning('Unable to fetch serial for device %s', device)
        continue
      try:
        subprocess.check_call([path_to_adb, '-s', serial, 'reboot'])
        logging.debug('Rebooting device %s.', device)
      except subprocess.CalledProcessError:
        logging.exception('Unable to reboot device %s', device.serial)
  finally:
    try:
      subprocess.check_call([path_to_adb, 'kill-server'])
    except subprocess.CalledProcessError:
      logging.exception('Unable to kill adb server.')


def get_host_uptime():
  """Returns host uptime in minutes."""
  with open('/proc/uptime') as f:
    uptime = float(f.readline().split()[0])
  return uptime / 60


def reboot_host():
  # Docker'ed android hosts should have /sbin/reboot as password-less sudo.
  cmd = ['sudo', '-n', '/sbin/reboot']
  try:
    subprocess.check_call(cmd)
  except subprocess.CalledProcessError:
    logging.exception('Unable to reboot host.')


def add_device(docker_client, android_devices, args):
  # pylint: disable=unused-argument
  for device in android_devices:
    container = docker_client.get_container(device)
    if container is not None:
      container.add_device(device)
    else:
      logging.error('Unable to add device %s: no running container.', device)


def launch(docker_client, android_devices, args):
  running_containers = docker_client.get_running_containers()
  # Reboot the host if needed. Will attempt to kill all running containers
  # gracefully before triggering reboot.
  host_uptime = get_host_uptime()
  if host_uptime > args.max_host_uptime:
    logging.debug('Host uptime over max uptime (%d > %d)',
                  host_uptime, args.max_host_uptime)
    if len(running_containers) > 0:
      if host_uptime - args.max_host_uptime > 60:
        logging.warning(
            'Host uptime exceeds grace period of 60 min. Rebooting host now '
            'despite %d running containers.', len(running_containers))
        reboot_host()
      else:
        logging.debug(
            'Still %d containers running. Shutting them down first.',
            len(running_containers))
        for c in running_containers:
          c.kill_swarming_bot()
    else:
      logging.debug('No running containers. Rebooting host now.')
      reboot_host()
  else:  # Host uptime < max host uptime.
    # TODO(bpastene): Maybe use py-adb instead? Need to investigate how a
    # device handles pontential flip-flopping of remote session IDs.
    if not os.path.exists(args.path_to_adb):
      logging.error('adb path %s does not exist.', args.path_to_adb)
      return 1

    # Fetch the image from the registry if it's not present locally.
    image_url = (_REGISTRY_URL + '/' + args.registry_project + '/' +
        args.image_name)
    if not docker_client.has_image(image_url):
      logging.debug('Local image missing. Fetching %s ...', image_url)
      docker_client.login(_REGISTRY_URL, args.credentials_file)
      docker_client.pull(image_url)
      logging.debug('Image %s fetched.', image_url)

    # Cleanup old containers that were stopped from a previous run.
    # TODO(bpastene): Maybe enable auto cleanup with the -rm option?
    docker_client.delete_stopped_containers()

    # Send SIGTERM to bots in containers that have been running for too long.
    docker_client.stop_old_containers(
        running_containers, args.max_container_uptime)

    # Create a container for each device that doesn't already have one.
    needs_reboot = docker_client.create_missing_containers(
        running_containers, android_devices, image_url)

    # Reboot all devices that were just granted a new container to trigger the
    # needed udev events.
    # TODO(bpastene): Maybe pause all running containers before-hand? Spawning
    # up adb on the host might interfere with tests running inside other
    # containers.
    if needs_reboot:
      reboot_devices(needs_reboot, args.path_to_adb)


def main():
  parser = argparse.ArgumentParser(
      description='Manage docker containers that wrap an android device.')
  parser.add_argument(
      '-v', '--verbose', action='store_true', help='Enable verbose logging.')
  parser.add_argument(
      '--device', action='append', dest='devices', default=[],
      help='Serial number of device whose container is to be managed. Defaults '
      'to ALL local devices.')
  subparsers = parser.add_subparsers()

  add_subparser = subparsers.add_parser(
      'add_device', help='Give a container access to its device.'
  )
  add_subparser.set_defaults(func=add_device)

  launch_subparser = subparsers.add_parser(
      'launch',
      help='Ensures the specified devices have a running container. Will send '
           'a kill signal to containers that exceed max uptime.'
  )
  launch_subparser.set_defaults(func=launch)
  launch_subparser.add_argument(
      '--max-container-uptime', type=int, default=60 * 4,
      help='Max uptime of a container, in minutes.')
  launch_subparser.add_argument(
      '--max-host-uptime', type=int, default=60 * 24,
      help='Max uptime of the host, in minutes.')
  launch_subparser.add_argument(
      '--image-name', default='android_docker:latest',
      help='Name of docker image to launch from.')
  launch_subparser.add_argument(
      '--registry-project', default='chromium-container-registry',
      help='Name of gcloud project id for the container registry.')
  launch_subparser.add_argument(
      '--credentials-file',
      default='/creds/service_accounts/'
              'service-account-container_registry_puller.json',
      help='Path to service account json file used to access the gcloud '
           'container registry.')
  launch_subparser.add_argument(
      '--path-to-adb',
      default=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'adb'),
      help='Path to adb binary. Used to reboot devices on container startup.')
  args = parser.parse_args()

  logger = logging.getLogger()
  logger.setLevel(logging.DEBUG if args.verbose else logging.WARNING)
  log_fmt = logging.Formatter(
      '%(asctime)s.%(msecs)03d %(levelname)s %(message)s',
      datefmt='%y%m%d %H:%M:%S')

  # Udev-triggered runs of this script run as root while the crons run as
  # non-root. Manually set umask to ensure the world can read/write to the log
  # files even if they're owned by root.
  os.umask(0o000)
  file_handler = logging.handlers.RotatingFileHandler(
      '/tmp/android_containers.log', maxBytes=10 * 1024 * 1024, backupCount=5)
  file_handler.setFormatter(log_fmt)
  logger.addHandler(file_handler)
  stdout_handler = logging.StreamHandler(sys.stdout)
  logger.addHandler(stdout_handler)

  docker_client = containers.DockerClient()
  android_devices = usb_device.get_android_devices(args.devices)

  args.func(docker_client, android_devices, args)

  return 0


if __name__ == '__main__':
  if sys.platform != 'linux2':
    print 'Only supported on linux.'
    sys.exit(1)
  try:
    sys.exit(main())
  except Exception as e:
    logging.exception('Exception:')
    raise e