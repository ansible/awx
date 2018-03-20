/* Copyright (c) 2017 Red Hat, Inc. */

const templateUrl = require('~network-ui/debug.partial.svg');

function debug () {
  return {
      restrict: 'A',
      templateUrl,
      link: function(){
          $('.NetworkUI__debug-text').each(function(index, option){
             let startingY = 15;
             let offset = 20;
             let y = startingY + (index * offset);
             option.setAttribute('y', y);
          });
      }
  };
}

exports.debug = debug;
