/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import { templateUrl } from '../../shared/template-url/template-url.factory';
import InventoriesManage from './inventory-manage.controller';
import BreadcrumbsController from './breadcrumbs/breadcrumbs.controller';
import HostsListController from './hosts/hosts-list.controller';
import GroupsListController from './groups/groups-list.controller';

export default {
    name: 'inventoryManage',
    data: {
        socket: {
            "groups": {
                "jobs": ["status_changed"]
            }
        }
    },
    // instead of a single 'searchPrefix' attribute, provide hard-coded search params
    url: '/inventories/:inventory_id/manage?{group:int}{group_search:queryset}{host_search:queryset}',
    params: {
        group: {
            array: true
        },
        group_search: {
            value: {
                page_size: '20',
                page: '1',
                order_by: 'name',
            },
            squash: true
        },
        host_search: {
            value: {
                page_size: '20',
                page: '1',
                order_by: 'name',
            },
            squash: true
        }
    },
    ncyBreadcrumb: {
        skip: true // Never display this state in ncy-breadcrumb.
    },
    // enforce uniqueness in group param
    onEnter: function($stateParams) {
        $stateParams.group = _.uniq($stateParams.group);
    },
    resolve: {
        groupsUrl: ['InventoryManageService', '$stateParams', function(InventoryManageService, $stateParams) {
            return $stateParams.group && $stateParams.group.length > 0 ?
                // nested context - provide this node's children
                InventoryManageService.childGroupsUrl(_.last($stateParams.group)) :
                // root context - provide root nodes
                InventoryManageService.rootGroupsUrl($stateParams.inventory_id);
        }],
        hostsUrl: ['InventoryManageService', '$stateParams', function(InventoryManageService, $stateParams) {
            return $stateParams.group && $stateParams.group.length > 0 ?
                // nested context - provide all hosts managed by nodes
                InventoryManageService.childHostsUrl(_.last($stateParams.group)) :
                // root context - provide all hosts in an inventory
                InventoryManageService.rootHostsUrl($stateParams.inventory_id);
        }],
        inventoryData: ['InventoryManageService', '$stateParams', function(InventoryManageService, $stateParams) {
            return InventoryManageService.getInventory($stateParams.inventory_id).then(res => res.data);
        }],
        breadCrumbData: ['InventoryManageService', '$stateParams', function(InventoryManageService, $stateParams) {
            return $stateParams.group && $stateParams.group.length > 0 ?
                // nested context - provide breadcrumb data
                InventoryManageService.getBreadcrumbs($stateParams.group).then(res => res.data.results) :
                // root context
                false;
        }],
        groupsDataset: ['InventoryGroups', 'QuerySet', '$stateParams', 'groupsUrl', (list, qs, $stateParams, groupsUrl) => {
            let path = groupsUrl;
            return qs.search(path, $stateParams[`${list.iterator}_search`]);
        }],
        hostsDataset: ['InventoryHosts', 'QuerySet', '$stateParams', 'hostsUrl', (list, qs, $stateParams, hostsUrl) => {
            let path = hostsUrl;
            return qs.search(path, $stateParams[`${list.iterator}_search`]);
        }]
    },
    views: {
        // target the ui-view with name "groupBreadcrumbs" at the root view
        'groupBreadcrumbs@': {
            controller: BreadcrumbsController,
            templateUrl: templateUrl('inventories/manage/breadcrumbs/breadcrumbs')
        },
        // target the ui-view with name "list" at the root view
        'list@': {
            templateUrl: templateUrl('inventories/manage/inventory-manage'),
            controller: InventoriesManage
        },
        // target ui-views with name@inventoryManage state
        'groupsList@inventoryManage': {
            templateProvider: function(InventoryGroups, generateList, $templateRequest) {
                let html = generateList.build({
                    list: InventoryGroups,
                    mode: 'edit'
                });
                html = generateList.wrapPanel(html);
                // I'm so sorry
                // group delete modal
                return $templateRequest(templateUrl('inventories/manage/groups/groups-list')).then((template) => {
                    return html.concat(template);
                });
            },
            controller: GroupsListController
        },
        'hostsList@inventoryManage': {
            templateProvider: function(InventoryHosts, generateList) {
                let html = generateList.build({
                    list: InventoryHosts,
                    mode: 'edit'
                });
                return generateList.wrapPanel(html);
            },
            controller: HostsListController
        }
    }
};
