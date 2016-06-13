/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
import {templateUrl} from '../../../shared/template-url/template-url.factory';
import addController from './hosts-add.controller';
import editController from './hosts-edit.controller';

var ManageHostsEdit = {
    name: 'inventoryManage.editHost',
    route: '/edit-host?host_id',
    ncyBreadcrumb: {
        label: "EDIT {{host.name}}",
    },
    data: {
        mode: 'edit'
    },
    resolve: {
        host: ['$stateParams', 'HostManageService', function($stateParams, HostManageService){
            return HostManageService.get({id: $stateParams.host_id}).then(function(res){
                return res.data.results[0];
            });
        }]
    },
    views: {
        'form@inventoryManage': {
            controller: editController,
            templateUrl: templateUrl('inventories/manage/hosts/hosts-form'),
        }
    }
};
var ManageHostsAdd = {
    name: 'inventoryManage.addHost',
    route: '/add-host',
    // use a query string to break regex search
    ncyBreadcrumb: {
        label: "ADD HOST"
    },
    data: {
        mode: 'add'
    },
    views: {
        'form@inventoryManage': {
            controller: addController,
            templateUrl: templateUrl('inventories/manage/hosts/hosts-form'),
        }
    }
};
export {ManageHostsAdd, ManageHostsEdit};
