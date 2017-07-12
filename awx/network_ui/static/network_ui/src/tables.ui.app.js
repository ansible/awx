
//console.log = function () { };
var angular = require('angular');
var TablesUIController = require('./tables.ui.controller.js');
var awxTablesUI = require('./tables.ui.directive.js');

var tablesUI = angular.module('tablesUI', [])
    .controller('TablesUIController', TablesUIController.TablesUIController)
    .directive('awxTablesUi', awxTablesUI.awxTablesUI);

exports.tablesUI = tablesUI;
