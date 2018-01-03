/* Copyright (c) 2017 Red Hat, Inc. */

const templateUrl = require('~network-ui/task_status.partial.svg');

function taskStatus () {
  return { restrict: 'A', templateUrl};
}
exports.taskStatus = taskStatus;
