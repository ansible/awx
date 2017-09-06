/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import credentialTypesList from './list/main';
import credentialTypesAdd from './add/main';
import credentialTypesEdit from './edit/main';
import list from './credential-types.list';
import form from './credential-types.form';
import { N_ } from '../i18n';

export default
angular.module('credentialTypes', [
        credentialTypesList.name,
        credentialTypesAdd.name,
        credentialTypesEdit.name
    ])
    .factory('CredentialTypesList', list)
    .factory('CredentialTypesForm', form)
    .config(['$stateProvider', 'stateDefinitionsProvider',
        function($stateProvider, stateDefinitionsProvider) {
            let stateDefinitions = stateDefinitionsProvider.$get();

            $stateProvider.state({
                name: 'credentialTypes',
                url: '/credential_type',
                lazyLoad: () => stateDefinitions.generateTree({
                    parent: 'credentialTypes',
                    modes: ['add', 'edit'],
                    list: 'CredentialTypesList',
                    form: 'CredentialTypesForm',
                    controllers: {
                        list: 'CredentialTypesListController',
                        add: 'CredentialTypesAddController',
                        edit: 'CredentialTypesEditController'
                    },
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'credential_type'
                    },
                    ncyBreadcrumb: {
                        label: N_('CREDENTIAL TYPES')
                    }
                })
            });
        }
    ]);
