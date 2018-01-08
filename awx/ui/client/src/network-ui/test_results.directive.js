/* Copyright (c) 2018 Red Hat, Inc. */

const templateUrl = require('~network-ui/test_results.partial.svg');

function test_results () {
  return { restrict: 'A', templateUrl};
}
exports.test_results = test_results;
