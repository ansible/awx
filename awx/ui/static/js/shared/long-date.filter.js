/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

angular.module('longDateFilter', []).filter('longDate', function() {
  return function(input) {

      // navigator.language is available in all modern browsers.
      // however navigator.languages is a new technology that
      // lists the user's preferred languages, the first in the array
      // being the user's top choice. navigator.languages is currently
      // comptabile with chrome>v32, ffox>32, but not IE/Safari
    var lang = navigator.languages ? navigator.languages[0] : (navigator.language || navigator.userLanguage),
        date = moment(input).locale(lang);
    return date.format('l LTS');
  };
});
