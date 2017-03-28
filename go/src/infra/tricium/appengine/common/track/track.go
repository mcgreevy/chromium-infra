// Copyright 2016 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

// Package track implements shared tracking functionality for the Tricium service modules.
package track

import (
	"time"

	ds "github.com/luci/gae/service/datastore"

	"infra/tricium/api/v1"
)

// Run tracks the processing of one analysis request.
type Run struct {
	// LUCI datastore fields.
	ID int64 `gae:"$id"`
	// Time when the corresponding request was received, time recorded in the reporter.
	Received time.Time
	// State of this run; received, launched, or done-*, with done indicating success.
	State tricium.State
	// The project of the request.
	Project string
}

// ServiceRequest lists the fields included in a request to the Tricium service.
//
// Stored with 'Run' as parent and is read-only.
type ServiceRequest struct {
	// LUCI datastore fields.
	ID     string  `gae:"$id"`
	Parent *ds.Key `gae:"$parent"`
	// Tricium connected project receiving the request.
	Project string
	// File paths listed in the request.
	Paths []string `gae:",noindex"`
	// Git repository hosting files in the request.
	GitRepo string `gae:",noindex"`
	// Git ref to use in the Git repo.
	GitRef string `gae:",noindex"`
}

// AnalyzerInvocation tracks the execution of an analyzer.
//
// This may happen in one or more worker invocations, each running on different platforms.
// Stored with 'Run' as parent.
type AnalyzerInvocation struct {
	// LUCI datastore fields.
	ID     string  `gae:"$id"`
	Parent *ds.Key `gae:"$parent"`
	// Name of the analyzer. The workflow for a run may have several
	// workers for one analyzer, each running on different platforms.
	Name string
	// State of this analyzer run; running, success, or failure.
	// This state is an aggregation of the run state of analyzer workers.
	State tricium.State
}

// WorkerInvocation tracks the execution of a worker.
//
// Stored with 'AnalyzerInvocation' as parent.
type WorkerInvocation struct {
	// LUCI datastore fields.
	ID     string  `gae:"$id"`
	Parent *ds.Key `gae:"$parent"`
	// Name of the worker. Same as that used in the workflow configuration.
	Name string
	// State of this worker run; running, success, or failure.
	State tricium.State
	// Platform this worker is producing results for.
	Platform tricium.Platform_Name
	// Isolate server URL.
	IsolateServerURL string `gae:",noindex"`
	// Hash to the isolated input provided to the corresponding swarming task.
	IsolatedInput string `gae:",noindex"`
	// Hash to the isolated output collected from the corresponding swarming task.
	IsolatedOutput string `gae:",noindex"`
	// Names of workers succeeding this worker in the workflow.
	Next []string `gae:",noindex"`
	//  Exit code of the corresponding swarming task.
	ExitCode int
	// Swarming server URL.
	SwarmingURL string `gae:",noindex"`
	// Swarming task ID.
	TaskID string `gae:",noindex"`
	// Number of result comments produced by this worker.
	NumResultComments int
}

// WorkerResult tracks the results from a worker.
//
// Stored with 'WorkerInvocation' as parent.
type WorkerResult struct {
	// LUCI datastore fields.
	ID     string  `gae:"$id"`
	Parent *ds.Key `gae:"$parent"`
	// Tricium result encoded as JSON.
	Result string `gae:",noindex"`
}
