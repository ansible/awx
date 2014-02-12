'use strict';

angular.module('gdi2290.gravatar-filter', [])
.filter('gravatar', function(md5) {
  var cache = {};
  return function(text, defaultText) {
    if (!cache[text]) {
      defaultText = (defaultText) ? md5.createHash(defaultText.toString().toLowerCase()) : '';
      cache[text] = (text) ? md5.createHash(text.toString().toLowerCase()) : defaultText;
    }
    return cache[text];
  };
});
