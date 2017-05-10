
//console.log = function () { };
var NetworkUIController = require('./network.ui.controller.js');
var cursor = require('./cursor.directive.js');
var touch = require('./touch.directive.js');
var router = require('./router.directive.js');
var switchd = require('./switch.directive.js');
var host = require('./host.directive.js');
var link = require('./link.directive.js');
var rack = require('./rack.directive.js');
var defaultd = require('./default.directive.js');
var quadrants = require('./quadrants.directive.js');
var stencil = require('./stencil.directive.js');
var layer = require('./layer.directive.js');
var button = require('./button.directive.js');
var statusLight = require('./status.light.directive.js');
var taskStatus = require('./task.status.directive.js');
var debug = require('./debug.directive.js');
var awxNetworkUI = require('./network.ui.directive.js');

var app = angular.module('networkUI', [
        'monospaced.mousewheel',
        'ngTouch'
    ])
    .controller('NetworkUIController', NetworkUIController.NetworkUIController)
    .directive('cursor', cursor.cursor)
    .directive('touch', touch.touch)
    .directive('debug', debug.debug)
    .directive('router', router.router)
    .directive('switch', switchd.switchd)
    .directive('host', host.host)
    .directive('link', link.link)
    .directive('rack', rack.rack)
    .directive('default', defaultd.defaultd)
    .directive('quadrants', quadrants.quadrants)
    .directive('stencil', stencil.stencil)
    .directive('layer', layer.layer)
    .directive('button', button.button)
    .directive('statusLight', statusLight.statusLight)
    .directive('taskStatus', taskStatus.taskStatus)
    .directive('awxNetworkUi', awxNetworkUI.awxNetworkUI);

exports.app = app;
