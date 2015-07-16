/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

angular.module('sanitizeFilter', []).filter('sanitize', function() {
  return function(input) {
    input = input.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/'/g, "&apos;").replace(/"/g, "&quot;");
    return input;
  };
});
