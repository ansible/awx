/* Copyright (c) 2017 Red Hat, Inc. */

//console.log = function () { };
var angular = require('angular');
var NetworkWidgetsController = require('./network.widgets.controller.js');
var cursor = require('./cursor.directive.js');
var touch = require('./touch.directive.js');
var router = require('./router.directive.js');
var switchd = require('./switch.directive.js');
var host = require('./host.directive.js');
var link = require('./link.directive.js');
var stream = require('./stream.directive.js');
var rack = require('./rack.directive.js');
var rackIcon = require('./rack.icon.directive.js');
var group = require('./group.directive.js');
var site = require('./site.directive.js');
var siteIcon = require('./site.icon.directive.js');
var process = require('./process.directive.js');
var configuration = require('./configuration.directive.js');
var map = require('./map.directive.js');
var deviceDetail = require('./device.detail.directive.js');
var defaultd = require('./default.directive.js');
var quadrants = require('./quadrants.directive.js');
var stencil = require('./stencil.directive.js');
var layer = require('./layer.directive.js');
var button = require('./button.directive.js');
var inventoryToolbox = require('./inventory.toolbox.directive.js');
var inventoryToolboxClipPath = require('./inventory.toolbox.clip.path.directive.js');
var statusLight = require('./status.light.directive.js');
var taskStatus = require('./task.status.directive.js');
var debug = require('./debug.directive.js');
var awxNetworkWidgets = require('./network.widgets.directive.js');

var networkWidgets = angular.module('networkWidgets', [
        'monospaced.mousewheel',
        'ngTouch'
    ])
    .controller('NetworkWidgetsController', NetworkWidgetsController.NetworkWidgetsController)
    .directive('awxNetCursor', cursor.cursor)
    .directive('awxNetTouch', touch.touch)
    .directive('awxNetDebug', debug.debug)
    .directive('awxNetRouter', router.router)
    .directive('awxNetSwitch', switchd.switchd)
    .directive('awxNetHost', host.host)
    .directive('awxNetLink', link.link)
    .directive('awxNetStream', stream.stream)
    .directive('awxNetRack', rack.rack)
    .directive('awxNetGroup', group.group)
    .directive('awxNetSite', site.site)
    .directive('awxNetSiteIcon', siteIcon.siteIcon)
    .directive('awxNetRackIcon', rackIcon.rackIcon)
    .directive('awxNetProcess', process.process)
    .directive('awxNetConfiguration', configuration.configuration)
    .directive('awxNetMap', map.map)
    .directive('awxNetDeviceDetail', deviceDetail.deviceDetail)
    .directive('awxNetDefault', defaultd.defaultd)
    .directive('awxNetQuadrants', quadrants.quadrants)
    .directive('awxNetStencil', stencil.stencil)
    .directive('awxNetLayer', layer.layer)
    .directive('awxNetButton', button.button)
    .directive('awxNetInventoryToolbox', inventoryToolbox.inventoryToolbox)
    .directive('awxNetInventoryToolboxClipPath', inventoryToolboxClipPath.inventoryToolboxClipPath)
    .directive('awxNetStatusLight', statusLight.statusLight)
    .directive('awxNetTaskStatus', taskStatus.taskStatus)
    .directive('awxNetworkWidgets', awxNetworkWidgets.awxNetworkWidgets);

exports.networkWidgets = networkWidgets;
