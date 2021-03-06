# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from recipe_engine.recipe_api import Property

DEPS = [
  'depot_tools/bot_update',
  'depot_tools/gclient',
  'depot_tools/git',
  'depot_tools/presubmit',
  'depot_tools/tryserver',
  'recipe_engine/context',
  'recipe_engine/json',
  'recipe_engine/path',
  'recipe_engine/platform',
  'recipe_engine/properties',
  'recipe_engine/python',
  'recipe_engine/step',
]

PROPERTIES = {
  'presubmit': Property(
    default=False,
    kind=bool,
    help=(
      "if set, will run presubmit for the luci-go repo, otherwise runs tests."
    )),

  'GOARCH': Property(
    default=None,
    kind=str,
    help="set GOARCH environment variable for go build+test"),
}

LUCI_GO_PATH_IN_INFRA = 'infra/go/src/github.com/luci/luci-go'


def _run_presubmit(api, patch_root, bot_update_step):
  got_revision_properties = api.bot_update.get_project_revision_properties(
      LUCI_GO_PATH_IN_INFRA)
  upstream = bot_update_step.json.output['properties'].get(
      got_revision_properties[0])
  # The presubmit must be run with proper Go environment.
  # infra/go/env.py takes care of this.
  presubmit_cmd = [
    'python',  # env.py will replace with this its sys.executable.
    api.presubmit.presubmit_support_path,
    '--root', api.path['start_dir'].join(patch_root),
    '--commit',
    '--verbose', '--verbose',
    '--issue', api.properties['issue'],
    '--patchset', api.properties['patchset'],
    '--skip_canned', 'CheckRietveldTryJobExecution',
    '--skip_canned', 'CheckTreeIsOpen',
    '--skip_canned', 'CheckBuildbotPendingBuilds',
    '--rietveld_url', api.properties['rietveld'],
    '--rietveld_fetch',
    '--upstream', upstream,
    '--rietveld_email', ''
  ]
  with api.context(env={'PRESUBMIT_BUILDER': '1'}):
    api.python('presubmit', api.path['checkout'].join('go', 'env.py'),
               presubmit_cmd)


def _commit_change(api, patch_root):
  with api.context(cwd=api.path['start_dir'].join(patch_root)):
    api.git('-c', 'user.email=commit-bot@chromium.org',
            '-c', 'user.name=The Commit Bot',
            'commit', '-a', '-m', 'Committed patch',
            name='commit git patch')


def RunSteps(api, presubmit, GOARCH):
  api.gclient.set_config('luci_go')
  # patch_root must match the luci-go repo, not infra checkout.
  patch_root = LUCI_GO_PATH_IN_INFRA
  bot_update_step = api.bot_update.ensure_checkout(patch_root=patch_root)

  if presubmit:
    _commit_change(api, patch_root)
  api.gclient.runhooks()

  env = {}
  if GOARCH is not None:
    env['GOARCH'] = GOARCH

  with api.context(env=env):
    # This downloads the third parties, so that the next step doesn't have junk
    # output in it.
    api.python(
        'go third parties',
        api.path['checkout'].join('go', 'env.py'),
        ['go', 'version'],
        infra_step=True)

    if presubmit:
      with api.tryserver.set_failure_hash():
        _run_presubmit(api, patch_root, bot_update_step)
    else:
      api.python(
          'go build',
          api.path['checkout'].join('go', 'env.py'),
          ['go', 'build', 'github.com/luci/luci-go/...'])

      api.python(
          'go test',
          api.path['checkout'].join('go', 'env.py'),
          ['go', 'test', 'github.com/luci/luci-go/...'])


def GenTests(api):
  yield (
    api.test('luci_go') +
    api.properties.git_scheduled(
        path_config='kitchen',
        buildername='luci-go-linux64',
        buildnumber=123,
        mastername='chromium.infra',
        repository=('https://chromium.googlesource.com/external/github.com/'
                    'luci/luci-go'),
    )
  )

  yield (
    api.test('presubmit_try_job') +
    api.properties.tryserver(
        path_config='kitchen',
        mastername='tryserver.infra',
        buildername='Luci-go Presubmit',
        presubmit=True,
    ) + api.step_data('presubmit', api.json.output([[]]))
  )

  yield (
    api.test('override_GOARCH') +
    api.platform('linux', 64) +
    api.properties.tryserver(
        path_config='kitchen',
        mastername='tryserver.infra',
        buildername='Luci-go 32-on-64 Tests',
        GOARCH='386',
    )
  )

