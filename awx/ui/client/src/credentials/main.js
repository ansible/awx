/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import ownerList from './ownerList.directive';
import CredentialsList from './list/credentials-list.controller';
import CredentialsAdd from './add/credentials-add.controller';
import CredentialsEdit from './edit/credentials-edit.controller';
import { N_ } from '../i18n';

export default
    angular.module('credentials', [])
        .directive('ownerList', ownerList)
        .controller('CredentialsList', CredentialsList)
        .controller('CredentialsAdd', CredentialsAdd)
        .controller('CredentialsEdit', CredentialsEdit)
        .config(['$stateProvider', 'stateDefinitionsProvider',
            function($stateProvider, stateDefinitionsProvider) {
                let stateDefinitions = stateDefinitionsProvider.$get();

                // lazily generate a tree of substates which will replace this node in ui-router's stateRegistry
                // see: stateDefinition.factory for usage documentation
                $stateProvider.state({
                    name: 'credentials',
                    url: '/credentials',
                    lazyLoad: () => stateDefinitions.generateTree({
                        parent: 'credentials',
                        modes: ['add', 'edit'],
                        list: 'CredentialList',
                        form: 'CredentialForm',
                        controllers: {
                            list: CredentialsList,
                            add: CredentialsAdd,
                            edit: CredentialsEdit
                        },
                        data: {
                            activityStream: true,
                            activityStreamTarget: 'credential'
                        },
                        ncyBreadcrumb: {
                            parent: 'setup',
                            label: N_('CREDENTIALS')
                        }
                    })
                });
            }
        ]);
