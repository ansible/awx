
//console.log = function () { };
var angular = require('angular');
var NetworkUIController = require('./network.ui.controller.js');
var cursor = require('./cursor.directive.js');
var touch = require('./touch.directive.js');
var router = require('./router.directive.js');
var switchd = require('./switch.directive.js');
var host = require('./host.directive.js');
var link = require('./link.directive.js');
var rack = require('./rack.directive.js');
var group = require('./group.directive.js');
var map = require('./map.directive.js');
var deviceDetail = require('./device.detail.directive.js');
var defaultd = require('./default.directive.js');
var quadrants = require('./quadrants.directive.js');
var stencil = require('./stencil.directive.js');
var layer = require('./layer.directive.js');
var button = require('./button.directive.js');
var statusLight = require('./status.light.directive.js');
var taskStatus = require('./task.status.directive.js');
var debug = require('./debug.directive.js');
var awxNetworkUI = require('./network.ui.directive.js');

var networkUI = angular.module('networkUI', [
        'monospaced.mousewheel',
        'ngTouch'
    ])
    .controller('NetworkUIController', NetworkUIController.NetworkUIController)
    .directive('awxNetCursor', cursor.cursor)
    .directive('awxNetTouch', touch.touch)
    .directive('awxNetDebug', debug.debug)
    .directive('awxNetRouter', router.router)
    .directive('awxNetSwitch', switchd.switchd)
    .directive('awxNetHost', host.host)
    .directive('awxNetLink', link.link)
    .directive('awxNetRack', rack.rack)
    .directive('awxNetGroup', group.group)
    .directive('awxNetMap', map.map)
    .directive('awxNetDeviceDetail', deviceDetail.deviceDetail)
    .directive('awxNetDefault', defaultd.defaultd)
    .directive('awxNetQuadrants', quadrants.quadrants)
    .directive('awxNetStencil', stencil.stencil)
    .directive('awxNetLayer', layer.layer)
    .directive('awxNetButton', button.button)
    .directive('awxNetStatusLight', statusLight.statusLight)
    .directive('awxNetTaskStatus', taskStatus.taskStatus)
    .directive('awxNetworkUi', awxNetworkUI.awxNetworkUI);

exports.networkUI = networkUI;
