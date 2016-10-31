/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import {templateUrl} from '../../../shared/template-url/template-url.factory';

export default {
    url: '/adhoc',
    params:{
        pattern: {
            value: 'all',
            squash: true
        }
    },
    name: 'inventoryManage.adhoc',
    views: {
        'form@inventoryManage': {
            templateUrl: templateUrl('inventories/manage/adhoc/adhoc'),
            controller: 'adhocController'
        }
    },
    ncyBreadcrumb: {
        label: "RUN COMMAND"
    }
};
