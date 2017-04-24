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
                    resolve: {
                        edit: {
                            credential_typeData: ['$state', '$stateParams', 'Rest', 'GetBasePath', 'ProcessErrors',
                                function($state, $stateParams, rest, getBasePath, ProcessErrors) {
                                    var credentialTypeId = $stateParams.credential_type_id;
                                    var url = getBasePath('credential_types') + credentialTypeId + '/';
                                    rest.setUrl(url);
                                    return rest.get()
                                        .then(function(data) {
                                            return data.data;
                                        }).catch(function(response) {
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: 'Error!',
                                                msg: 'Failed to get credential type info. GET returned status: ' +
                                                    response.status
                                            });
                                        });
                                }
                            ]
                        }
                    },
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'custom_inventory_script' // TODO: change to 'credential_type'...there's probably more work that needs to be done to hook up activity stream
                    },
                    ncyBreadcrumb: {
                        parent: 'setup',
                        label: N_('CREDENTIAL TYPES')
                    }
                })
            });
        }
    ]);
