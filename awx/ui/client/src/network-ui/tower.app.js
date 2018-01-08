/* Copyright (c) 2017 Red Hat, Inc. */

var angular = require('angular');

var tower = angular.module('tower', ['networkUI', 'ui.router']);

tower.config(function($stateProvider, $urlRouterProvider) {

    $urlRouterProvider.otherwise('/index');

    $stateProvider
        .state({
            name: 'index',
            url: '/index',
            template: '<ul><li><a href="#!/topology">Topology</a></li><li><a href="#!/tables">Tables</a></li></ul>'
        });

    $stateProvider
        .state({
            name: 'topology',
            url: '/topology',
            template: "<awx-network-ui></awx-network-ui>"
        });

    $stateProvider
        .state({
            name: 'tables',
            url: '/tables',
            template: "<awx-tables-ui></awx-tables-ui>"
        });
});

exports.tower = tower;

