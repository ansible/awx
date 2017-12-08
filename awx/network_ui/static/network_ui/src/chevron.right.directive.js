/* Copyright (c) 2017 Red Hat, Inc. */

function chevronRight () {
  return {
      restrict: 'A',
      templateUrl: '/static/network_ui/widgets/chevron_right.svg',
      scope: {
          actionIcon: '='
      }
  };
}
exports.chevronRight = chevronRight;
