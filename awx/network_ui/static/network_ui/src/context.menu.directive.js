/* Copyright (c) 2017 Red Hat, Inc. */

function contextMenu () {
  return {
      restrict: 'A',
      templateUrl: '/static/network_ui/widgets/context_menu.svg',
      scope: {
          contextMenu: '='
      }
  };
}
exports.contextMenu = contextMenu;
