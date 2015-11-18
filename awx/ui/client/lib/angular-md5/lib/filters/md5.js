'use strict';

angular.module('gdi2290.md5-filter', [])
.filter('md5', function(md5) {
  return function(text) {
    return (text) ? md5.createHash(text.toString().toLowerCase()) : text;
  };
});
