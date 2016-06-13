/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
import {templateUrl} from '../../../shared/template-url/template-url.factory';
import addController from './groups-add.controller';
import editController from './groups-edit.controller';

var ManageGroupsEdit = {
    name: 'inventoryManage.editGroup',
    route: '/edit-group?group_id',
    ncyBreadcrumb: {
        label: "{{group.name}}"
    },
    data: {
        mode: 'edit'
    },
    resolve: {
        groupData: ['$stateParams', 'GroupManageService', function($stateParams, GroupManageService){
            return GroupManageService.get({id: $stateParams.group_id}).then(res => res.data.results[0]);
        }],
        inventorySourceData: ['$stateParams', 'GroupManageService', function($stateParams, GroupManageService){
            return GroupManageService.getInventorySource({group: $stateParams.group_id}).then(res => res.data.results[0]);
        }]
    },
    views: {
        'form@inventoryManage': {
            controller: editController,
            templateUrl: templateUrl('inventories/manage/groups/groups-form'),
        }
    }
};
var ManageGroupsAdd = {
    name: 'inventoryManage.addGroup',
    route: '/add-group',
    // use a query string to break regex search
    ncyBreadcrumb: {
        label: "CREATE GROUP"
    },
    data: {
        mode: 'add'
    },
    views: {
        'form@inventoryManage': {
            controller: addController,
            templateUrl: templateUrl('inventories/manage/groups/groups-form'),
        }
    }
};
export {ManageGroupsAdd, ManageGroupsEdit};
