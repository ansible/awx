/* Copyright (c) 2017 Red Hat, Inc. */

const templateUrl = require('~network-ui/context_menu.partial.svg');

function contextMenu () {
  return {
      restrict: 'A',
      templateUrl,
      scope: {
          contextMenu: '='
      }
  };
}
exports.contextMenu = contextMenu;
