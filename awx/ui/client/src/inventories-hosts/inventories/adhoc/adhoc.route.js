/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import {templateUrl} from '../../../shared/template-url/template-url.factory';
 import { N_ } from '../../../i18n';

 function ResolveMachineCredentialType (GetBasePath, Rest, ProcessErrors) {
    Rest.setUrl(GetBasePath('credential_types') + '?kind=ssh');

    return Rest.get()
        .then(({ data }) => {
            return data.results[0].id;
        })
        .catch(({ data, status }) => {
            ProcessErrors(null, data, status, null, {
                hdr: 'Error!',
                msg: 'Failed to get credential type data: ' + status
            });
        });
}

ResolveMachineCredentialType.$inject = ['GetBasePath', 'Rest', 'ProcessErrors'];

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
    },
    resolve: {
        machineCredentialType: ResolveMachineCredentialType,
    }
};
