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

import userListRoute from './users.route';
import UserTokensListRoute from '../../features/users/tokens/users-tokens-list.route';
import UserTokensAddRoute from '../../features/users/tokens/users-tokens-add.route';
import UserTokensAddApplicationRoute from '../../features/users/tokens/users-tokens-add-application.route';

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
                let userAdd = stateDefinitions.generateTree({
                    name: 'users.add',
                    url: '/add',
                    modes: ['add'],
                    form: 'UserForm',
                    controllers: {
                        add: 'UsersAdd'
                    },
                    resolve: {
                        add: {
                            canAdd: ['rbacUiControlService', '$state', function(rbacUiControlService, $state) {
                                return rbacUiControlService.canAdd('users')
                                    .then(function(res) {
                                        return res.canAdd;
                                    })
                                    .catch(function() {
                                        $state.go('users');
                                    });
                            }],
                            resolvedModels: ['MeModel', '$q',  function(Me, $q) {
                                const promises= {
                                    me: new Me('get').then((me) => me.extend('get', 'admin_of_organizations'))
                                };
    
                                return $q.all(promises);
                            }]
                        }
                    }
                });

                let userEdit = stateDefinitions.generateTree({
                    name: 'users.edit',
                    url: '/:user_id',
                    modes: ['edit'],
                    form: 'UserForm',
                    parent: 'users',
                    controllers: {
                        edit: 'UsersEdit'
                    },
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'user'
                    },
                    breadcrumbs: { 
                        edit: "{{breadcrumb.user_name}}"
                    },
                    resolve: {
                        edit: {
                            resolvedModels: ['MeModel', '$q',  function(Me, $q) {
                                const promises= {
                                    me: new Me('get').then((me) => me.extend('get', 'admin_of_organizations'))
                                };

                                return $q.all(promises);
                            }]
                        }
                    },
                });
                
                return Promise.all([
                    userAdd, 
                    userEdit
                ]).then((generated) => {
                    return {
                        states: _.reduce(generated, (result, definition) => {
                            return result.concat(definition.states);
                        }, [
                            stateExtender.buildDefinition(userListRoute),
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
