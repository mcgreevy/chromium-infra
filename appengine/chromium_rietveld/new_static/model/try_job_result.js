// Copyright (c) 2014 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

"use strict";

function TryJobResult()
{
    this.steps = [];
    this.slave = "";
    this.url = "";
    this.master = "";
    this.timestamp = ""; // Date
    this.builder = "";
    this.clobber = false;
    this.project = "";
    this.reason = "";
    this.result = "";
    this.resultGroup = 0;
    // this.key = ""; // What is this for?
    this.requester = null; // User
    this.buildnumber = 0;
    this.revision = ""; // Number or HEAD
    this.summary = "";
    this.moreInfoUrl = "";
    Object.preventExtensions(this);
}

TryJobResult.RESULT = {
    "-1": "pending",
    "0": "success",
    "1": "warnings",
    "2": "failure",
    "3": "skipped",
    "4": "exception",
    "5": "retry",
    // It's not clear from the Rietveld code if pending is -1 or 6, the server seems to reply with -1?
    "6": "pending",
};

TryJobResult.GROUPS = {
    "pending": 1,
    "retry": 2,
    "success": 3,
    "skipped": 4,
    "warnings": 5,
    "failure": 5,
    "exception": 5,
};

TryJobResult.prototype.getDetailUrl = function()
{
    return this.url;
};

TryJobResult.prototype.parseData = function(data)
{
    var result = this;
    this.steps = data.tests || [];
    this.slave = data.slave || "";
    this.timestamp = Date.utc.create(data.timestamp);
    this.builder = data.builder || "";
    this.clobber = data.clobber || false;
    this.project = data.project || "";
    this.reason = data.reason || "";
    this.result = TryJobResult.RESULT[data.result] || "";
    this.resultGroup = TryJobResult.GROUPS[this.result] || 0;
    this.requester = new User(data.requester);
    this.buildnumber = parseInt(data.buildnumber, 10) || 0;
    this.revision = data.revision || "";
    this.url = data.url || "";
    this.master = data.master || "";

    var build_properties = JSON.parse(data.build_properties);
    this.summary = build_properties.summary || "";
    this.moreInfoUrl = build_properties.moreInfoURL || "";
};
