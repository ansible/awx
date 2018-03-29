/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import UsersList from './list/users-list.controller';
import UsersAdd from './add/users-add.controller';
import UsersEdit from './edit/users-edit.controller';
import UserForm from './users.form';
import UserList from './users.list';

import UserTokensListRoute from '../../features/users/tokens/users-tokens-list.route';
import UserTokensAddRoute from '../../features/users/tokens/users-tokens-add.route';
import UserTokensAddApplicationRoute from '../../features/users/tokens/users-tokens-add-application.route';

import { N_ } from '../i18n';

export default
angular.module('Users', [])
    .controller('UsersList', UsersList)
    .controller('UsersAdd', UsersAdd)
    .controller('UsersEdit', UsersEdit)
    .factory('UserForm', UserForm)
    .factory('UserList', UserList)
    .config(['$stateProvider', 'stateDefinitionsProvider', '$stateExtenderProvider',
        function($stateProvider, stateDefinitionsProvider, $stateExtenderProvider) {
            let stateDefinitions = stateDefinitionsProvider.$get();
            let stateExtender = $stateExtenderProvider.$get();

            function generateStateTree() {
                let userTree = stateDefinitions.generateTree({
                    parent: 'users',
                    modes: ['add', 'edit'],
                    list: 'UserList',
                    form: 'UserForm',
                    controllers: {
                        list: UsersList,
                        add: UsersAdd,
                        edit: UsersEdit
                    },
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'user'
                    },
                    resolve: {
                        edit: {
                            resolvedModels: ['MeModel', '$q',  function(Me, $q) {
                                const promises= {
                                    me: new Me('get').then((me) => me.extend('get', 'admin_of_organizations'))
                                };

                                return $q.all(promises);
                            }]
                        },
                        list: {
                            resolvedModels: ['MeModel', '$q',  function(Me, $q) {
                                const promises= {
                                    me: new Me('get')
                                };

                                return $q.all(promises);
                            }]
                        }
                    },
                    ncyBreadcrumb: {
                        label: N_('USERS')
                    }
                });

                return Promise.all([
                    userTree
                ]).then((generated) => {
                    return {
                        states: _.reduce(generated, (result, definition) => {
                            return result.concat(definition.states);
                        }, [
                            stateExtender.buildDefinition(UserTokensListRoute),
                            stateExtender.buildDefinition(UserTokensAddRoute),
                            stateExtender.buildDefinition(UserTokensAddApplicationRoute)
                        ])
                    };
                });
            }

            $stateProvider.state({
                name: 'users.**',
                url: '/users',
                lazyLoad: () => generateStateTree()
            });

        }
    ]);
