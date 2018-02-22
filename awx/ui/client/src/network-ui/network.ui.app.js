/* Copyright (c) 2017 Red Hat, Inc. */

import atFeaturesNetworking from './network-nav/main';
import networkDetailsDirective from './network-details/main';
import networkZoomWidget from './zoom-widget/main';

//console.log = function () { };
var angular = require('angular');
var NetworkUIController = require('./network.ui.controller.js');
var cursor = require('./cursor.directive.js');
var router = require('./router.directive.js');
var switchd = require('./switch.directive.js');
var host = require('./host.directive.js');
var link = require('./link.directive.js');
var chevronRight = require('./chevron.right.directive.js');
var chevronLeft = require('./chevron.left.directive.js');
var contextMenu = require('./context.menu.directive.js');
var contextMenuButton = require('./context.menu.button.directive.js');
var defaultd = require('./default.directive.js');
var quadrants = require('./quadrants.directive.js');
var inventoryToolbox = require('./inventory.toolbox.directive.js');
var debug = require('./debug.directive.js');
var test_results = require('./test_results.directive.js');
var awxNetworkUI = require('./network.ui.directive.js');

var networkUI = angular.module('networkUI', [
        'monospaced.mousewheel',
        atFeaturesNetworking,
        networkDetailsDirective.name,
        networkZoomWidget.name
    ])
    .controller('NetworkUIController', NetworkUIController.NetworkUIController)
    .directive('awxNetCursor', cursor.cursor)
    .directive('awxNetDebug', debug.debug)
    .directive('awxNetRouter', router.router)
    .directive('awxNetSwitch', switchd.switchd)
    .directive('awxNetHost', host.host)
    .directive('awxNetLink', link.link)
    .directive('awxNetChevronRightIcon', chevronRight.chevronRight)
    .directive('awxNetChevronLeftIcon', chevronLeft.chevronLeft)
    .directive('awxNetContextMenu', contextMenu.contextMenu)
    .directive('awxNetContextMenuButton', contextMenuButton.contextMenuButton)
    .directive('awxNetDefault', defaultd.defaultd)
    .directive('awxNetQuadrants', quadrants.quadrants)
    .directive('awxNetInventoryToolbox', inventoryToolbox.inventoryToolbox)
    .directive('awxNetTestResults', test_results.test_results)
    .directive('awxNetworkUi', awxNetworkUI.awxNetworkUI);

exports.networkUI = networkUI;
