/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
import {
    templateUrl
} from '../../../shared/template-url/template-url.factory';

import inventoryManageCopyCtrl from './copy.controller';

export default {
    copy: {
        name: 'inventoryManage.copy',
        route: '/copy',
        templateUrl: templateUrl('inventories/manage/copy/copy'),
        ncyBreadcrumb: {
            label: "COPY"
        },
        resolve: {
            features: ['FeaturesService', function(FeaturesService) {
                return FeaturesService.get();
            }],
        },
        controller: inventoryManageCopyCtrl,
        controllerAs: 'vm',
        bindToController: true,
    },
    copyGroup: {
        name: 'inventoryManage.copy.group',
        route: '/group/:group_id?groups',
        template: '<div><copy-groups></copy-groups></div>',
        data: {
            group_id: 'group_id',
        },
        ncyBreadcrumb: {
            label: "GROUP"
        },
        resolve: {
            features: ['FeaturesService', function(FeaturesService) {
                return FeaturesService.get();
            }]
        }
    },
    copyHost: {
        name: 'inventoryManage.copy.host',
        route: '/host/:host_id?groups',
        template: '<div><copy-hosts></copy-hosts></div>',
        data: {
            host_id: 'host_id',
        },
        ncyBreadcrumb: {
            label: "HOST"
        },
        resolve: {
            features: ['FeaturesService', function(FeaturesService) {
                return FeaturesService.get();
            }]
        }
    }
};
