/* Copyright (c) 2017 Red Hat, Inc. */

const templateUrl = require('~network-ui/context_menu_button.partial.svg');

function contextMenuButton () {
  return {
      restrict: 'A',
      templateUrl,
      scope: {
          contextMenuButton: '=',
          contextMenu: '='
      }
  };
}
exports.contextMenuButton = contextMenuButton;
