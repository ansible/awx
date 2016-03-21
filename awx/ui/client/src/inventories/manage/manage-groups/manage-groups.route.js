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
        name: 'inventoryManage.editGroup',
        route: '/:group_id/editGroup',
        templateUrl: templateUrl('inventories/manage/manage-groups/manage-groups'),
        data: {
            group_id: 'group_id',
            mode: 'edit'
        },
        ncyBreadcrumb: {
            label: "INVENTORY EDIT GROUPS"
        },
        resolve: {
            features: ['FeaturesService', function(FeaturesService) {
                return FeaturesService.get();
            }]
        }
    },

    add: {
        name: 'inventoryManage.addGroup',
        route: '/addGroup',
        templateUrl: templateUrl('inventories/manage/manage-groups/manage-groups'),
        ncyBreadcrumb: {
            label: "INVENTORY ADD GROUP"
        },
        data: {
            mode: 'add'
        },
        resolve: {
            features: ['FeaturesService', function(FeaturesService) {
                return FeaturesService.get();
            }]
        }
    },

};
