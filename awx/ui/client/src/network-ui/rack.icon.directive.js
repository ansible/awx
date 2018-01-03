/* Copyright (c) 2017 Red Hat, Inc. */

const templateUrl = require('~network-ui/rack_icon.partial.svg');

function rackIcon () {
  return { restrict: 'A', templateUrl};
}
exports.rackIcon = rackIcon;
