/* Copyright (c) 2017 Red Hat, Inc. */

const templateUrl = require('~network-ui/site_icon.partial.svg');

function siteIcon () {
  return { restrict: 'A', templateUrl};
}
exports.siteIcon = siteIcon;
