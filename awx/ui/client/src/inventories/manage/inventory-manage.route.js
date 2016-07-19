/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';
import InventoriesManage from './inventory-manage.controller';
import BreadcrumbsController from './breadcrumbs/breadcrumbs.controller';
import HostsListController from './hosts/hosts-list.controller';
import GroupsListController from './groups/groups-list.controller';

export default {
    name: 'inventoryManage',
    url: '/inventories/:inventory_id/manage?{group:int}{failed}',
    data: {
        activityStream: true,
        activityStreamTarget: 'inventory',
        activityStreamId: 'inventory_id'
    },
    params:{
        group:{
            array: true
        },
        failed:{
            value: 'false',
            squash: true
        }
    },
    ncyBreadcrumb: {
        skip: true // Never display this state in ncy-breadcrumb.
    },
    // enforce uniqueness in group param
    onEnter: function($stateParams){
        $stateParams.group = _.uniq($stateParams.group);
    },
    resolve: {
        groupsUrl: ['InventoryManageService', '$stateParams', function(InventoryManageService, $stateParams){
            return !$stateParams.group ?
                InventoryManageService.rootGroupsUrl($stateParams.inventory_id) :
                InventoryManageService.childGroupsUrl(_.last($stateParams.group));
        }],
        hostsUrl: ['InventoryManageService', '$stateParams', function(InventoryManageService, $stateParams){
            // at the root group level
            return !$stateParams.group ?
                InventoryManageService.rootHostsUrl($stateParams.inventory_id, $stateParams.failed) :
                InventoryManageService.childHostsUrl(_.last($stateParams.group, $stateParams.failed));
        }],
        inventoryData: ['InventoryManageService', '$stateParams', function(InventoryManageService, $stateParams){
            return InventoryManageService.getInventory($stateParams.inventory_id).then(res => res.data);
        }],
        breadCrumbData: ['InventoryManageService', '$stateParams', function(InventoryManageService, $stateParams){
            return ( (!$stateParams.group) ? false : InventoryManageService.getBreadcrumbs($stateParams.group).then(res => res.data.results));
        }]
    },
    views:{
        // target the ui-view with name "groupBreadcrumbs" at the root template level
        'groupBreadcrumbs@': {
            controller: BreadcrumbsController,
            templateUrl: templateUrl('inventories/manage/breadcrumbs/breadcrumbs')
        },
        '': {
            templateUrl: templateUrl('inventories/manage/inventory-manage'),
            controller: InventoriesManage
        },
        // target ui-views with name@inventoryManage template level
        'groupsList@inventoryManage': {
            templateUrl: templateUrl('inventories/manage/groups/groups-list'),
            controller: GroupsListController
        },
        'hostsList@inventoryManage': {
            template: '<div id="hosts-list" class="Panel"></div>',
            controller: HostsListController
        }
    }
};
