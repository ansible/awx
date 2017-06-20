/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import {templateUrl} from '../../../shared/template-url/template-url.factory';
 import { N_ } from '../../../i18n';

export default {
    url: '/adhoc',
    params:{
        pattern: {
            value: 'all',
            squash: true
        }
    },
    data: {
        formChildState: true
    },
    views: {
        'adhocForm@inventories': {
            templateUrl: templateUrl('inventories-hosts/inventories/adhoc/adhoc'),
            controller: 'adhocController'
        }
    },
    ncyBreadcrumb: {
        label: N_("RUN COMMAND")
    }
};
