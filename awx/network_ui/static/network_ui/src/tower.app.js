
var angular = require('angular');
var ui_router = require('angular-ui-router');

var tower = angular.module('tower', ['networkUI', 'ui.router']);

tower.config(function($stateProvider, $urlRouterProvider) {

    $urlRouterProvider.otherwise('/topology');

    $stateProvider
        .state({
            name: 'topology',
            url: '/topology',
            template: "<awx-network-ui></awx-network-ui>"
        });
});

exports.tower = tower;
exports.ui_router = ui_router;

