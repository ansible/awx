/* Copyright (c) 2017 Red Hat, Inc. */

const templateUrl = require('~network-ui/device_detail.partial.svg');

function deviceDetail () {
  return { restrict: 'A', templateUrl};
}
exports.deviceDetail = deviceDetail;
