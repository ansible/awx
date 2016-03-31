/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
import {
    templateUrl
} from '../../../shared/template-url/template-url.factory';

export default {
    edit: {
        name: 'inventoryManage.editHost',
        route: '/:host_id/editHost',
        templateUrl: templateUrl('inventories/manage/manage-hosts/manage-hosts'),
        data: {
            host_id: 'host_id',
            mode: 'edit'
        },
        ncyBreadcrumb: {
            label: "INVENTORY EDIT HOSTS"
        },
        resolve: {
            features: ['FeaturesService', function(FeaturesService) {
                return FeaturesService.get();
            }]
        }
    },

    add: {
        name: 'inventoryManage.addHost',
        route: '/addHost',
        templateUrl: templateUrl('inventories/manage/manage-hosts/manage-hosts'),
        data: {
            mode: 'add'
        },
        ncyBreadcrumb: {
            label: "INVENTORY ADD HOST"
        },
        resolve: {
            features: ['FeaturesService', function(FeaturesService) {
                return FeaturesService.get();
            }]
        }
    },

};
