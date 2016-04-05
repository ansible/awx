/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
import {
    templateUrl
} from '../../../shared/template-url/template-url.factory';

import inventoryManageCopyCtrl from './copy.controller';
import CopyGroupsCtrl from './copy-groups.controller';
import CopyHostsCtrl from './copy-hosts.controller';

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
        templateUrl: templateUrl('inventories/manage/copy/copy-groups'),
        data: {
            group_id: 'group_id',
        },
        ncyBreadcrumb: {
            label: "GROUP"
        },
        controller: CopyGroupsCtrl,
        controllerAs: 'vm',
        bindToController: true
    },
    copyHost: {
        name: 'inventoryManage.copy.host',
        route: '/host/:host_id?groups',
        templateUrl: templateUrl('inventories/manage/copy/copy-hosts'),
        data: {
            host_id: 'host_id',
        },
        ncyBreadcrumb: {
            label: "HOST"
        },
        controller: CopyHostsCtrl,
        controllerAs: 'vm',
        bindToController: true
    }
};
