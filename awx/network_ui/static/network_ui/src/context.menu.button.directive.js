/* Copyright (c) 2017 Red Hat, Inc. */

function contextMenuButton () {
  return {
      restrict: 'A',
      templateUrl: '/static/network_ui/widgets/context_menu_button.svg',
      scope: {
          contextMenuButton: '=',
          contextMenu: '='
      }
  };
}
exports.contextMenuButton = contextMenuButton;
