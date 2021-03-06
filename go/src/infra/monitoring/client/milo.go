// Copyright 2015 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package client

import (
	"bytes"
	"compress/gzip"
	"encoding/json"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	"golang.org/x/net/context"

	"infra/monitoring/messages"

	"github.com/luci/gae/service/urlfetch"
	"github.com/luci/luci-go/common/logging"
	"github.com/luci/luci-go/grpc/prpc"
	milo "github.com/luci/luci-go/milo/api/proto"
)

const (
	buildBotSvcName = "milo.Buildbot"
	miloHost        = "luci-milo.appspot.com"
)

type miloReader struct {
	reader
	host string
	// bCache is a map of build cache key to Build message.
	bCache map[string]*messages.Build
	// bLock protects bCache
	bLock sync.Mutex
}

// NewMiloReader returns a new reader implementation, which will read data from Milo.
func NewMiloReader(ctx context.Context, host string) (readerType, error) {
	if host == "" {
		host = miloHost
	}
	r, err := newReader(ctx, &http.Client{Transport: urlfetch.Get(ctx)})
	if err != nil {
		return nil, err
	}
	mr := &miloReader{
		host:   host,
		reader: *r,
	}

	// According to https://cloud.google.com/appengine/docs/standard/python/tools/using-local-server
	// we can detect if we're running on app engine with this.
	k, ok := os.LookupEnv("SERVER_SOFTWARE")
	// Don't use a cache on app engine, since these processes are long
	// lived.
	if !(ok || strings.HasPrefix(k, "Google App Engine/")) {
		mr.bCache = map[string]*messages.Build{}
	}
	return mr, nil
}

func (r *miloReader) Build(ctx context.Context, master *messages.MasterLocation, builder string, buildNum int64) (*messages.Build, error) {
	if r.bCache != nil {
		r.bLock.Lock()
		build, ok := r.bCache[cacheKeyForBuild(master, builder, buildNum)]
		r.bLock.Unlock()
		if ok {
			return build, nil
		}
	}

	miloClient := &prpc.Client{
		Host:    r.host,
		C:       &http.Client{Transport: urlfetch.Get(ctx)},
		Options: prpc.DefaultOptions(),
	}

	req := &milo.BuildbotBuildRequest{Master: master.Name(), Builder: builder, BuildNum: buildNum}
	resp := &milo.BuildbotBuildJSON{}

	if err := miloClient.Call(ctx, buildBotSvcName, "GetBuildbotBuildJSON", req, resp); err != nil {
		logging.Errorf(ctx, "error getting build %s/%s/%d: %v", master.Name(), builder, buildNum, err)
		return nil, err
	}

	build := &messages.Build{}
	if err := json.Unmarshal(resp.Data, build); err != nil {
		return nil, err
	}

	if build.Finished && r.bCache != nil {
		r.bLock.Lock()
		r.bCache[cacheKeyForBuild(master, builder, buildNum)] = build
		r.bLock.Unlock()
	}

	return build, nil
}

func (r *miloReader) LatestBuilds(ctx context.Context, master *messages.MasterLocation, builder string) ([]*messages.Build, error) {
	miloClient := &prpc.Client{
		Host:    r.host,
		C:       &http.Client{Transport: urlfetch.Get(ctx)},
		Options: prpc.DefaultOptions(),
	}

	req := &milo.BuildbotBuildsRequest{Master: master.Name(), Builder: builder, IncludeCurrent: true}
	resp := &milo.BuildbotBuildsJSON{}

	if err := miloClient.Call(ctx, buildBotSvcName, "GetBuildbotBuildsJSON", req, resp); err != nil {
		logging.Errorf(ctx, "error getting builds for %s/%s: %v", master.Name(), builder, err)
		return nil, err
	}

	builds := []*messages.Build{}
	for _, data := range resp.Builds {
		build := &messages.Build{}
		if err := json.Unmarshal(data.Data, build); err != nil {
			return nil, err
		}
		builds = append(builds, build)
	}
	return builds, nil
}

func (r *miloReader) BuildExtract(ctx context.Context, master *messages.MasterLocation) (*messages.BuildExtract, error) {
	ctx, cancelFunc := context.WithTimeout(ctx, 60*time.Second)
	defer cancelFunc()

	miloClient := &prpc.Client{
		Host:    r.host,
		C:       &http.Client{Transport: urlfetch.Get(ctx)},
		Options: prpc.DefaultOptions(),
	}

	req := &milo.MasterRequest{Name: master.Name()}
	resp := &milo.CompressedMasterJSON{}

	if err := miloClient.Call(ctx, buildBotSvcName, "GetCompressedMasterJSON", req, resp); err != nil {
		logging.Errorf(ctx, "error getting build extract for %s: %v", master.Name(), err)
		return nil, err
	}

	gzbs := bytes.NewBuffer(resp.Data)
	gsr, err := gzip.NewReader(gzbs)
	if err != nil {
		return nil, err
	}

	dec := json.NewDecoder(gsr)
	ret := &messages.BuildExtract{}
	if err := dec.Decode(ret); err != nil {
		return nil, err
	}

	return ret, nil
}
