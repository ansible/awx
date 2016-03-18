/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

// import {
//     templateUrl
// } from '../../../shared/template-url/template-url.factory';

import manageHostDirectiveController from './manage-hosts.controller'

export default {
    name: 'inventoryManage.manageHosts',
    route: '/managehosts',
    //template: '<div>SOMETHING</div>',
    views: {
        "manage@inventoryManage" : {
            template: '<div>the template from route</div>'
        }
    },

    // data: {
    //     activityStream: true,
    //     activityStreamTarget: 'inventory',
    //     activityStreamId: 'inventory_id'
    // },
    ncyBreadcrumb: {
        label: "INVENTORY MANAGE"
    },
    controller: manageHostDirectiveController,
    // resolve: {
    //     features: ['FeaturesService', function(FeaturesService) {
    //         return FeaturesService.get();
    //     }]
    // },
};
