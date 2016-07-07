/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
import {templateUrl} from '../../../shared/template-url/template-url.factory';
import addController from './manage-hosts-add.controller';
import editController from './manage-hosts-edit.controller';

var ManageHostsEdit = {
    name: 'inventoryManage.editHost',
    route: '/host/:host_id',
    controller: editController,
    templateUrl: templateUrl('inventories/manage/manage-hosts/manage-hosts'),
    ncyBreadcrumb: {
        label: "INVENTORY EDIT HOSTS"
    },
    data: {
        mode: 'edit'
    },
    resolve: {
        host: ['$stateParams', 'ManageHostsService', function($stateParams, ManageHostsService){
            return ManageHostsService.get({id: $stateParams.host_id}).then(function(res){
                return res.data.results[0];
            });
        }]
    }
};
var ManageHostsAdd = {
    name: 'inventoryManage.addHost',
    route: '/host/add',
    controller: addController,
    templateUrl: templateUrl('inventories/manage/manage-hosts/manage-hosts'),
    ncyBreadcrumb: {
        label: "INVENTORY ADD HOST"
    },
    data: {
        mode: 'add'
    }
};
export {ManageHostsAdd, ManageHostsEdit};
