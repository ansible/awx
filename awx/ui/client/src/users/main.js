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
import UserTokensListRoute from './users-tokens-list.route';
import UserTokensAddRoute from './users-tokens-add.route';
import UserTokensAddApplicationRoute from './users-tokens-add-application.route';
import TokensStrings from './tokens.strings';

import { N_ } from '../i18n';

export default
angular.module('Users', [])
    .controller('UsersList', UsersList)
    .controller('UsersAdd', UsersAdd)
    .controller('UsersEdit', UsersEdit)
    .factory('UserForm', UserForm)
    .factory('UserList', UserList)
    .service('TokensStrings', TokensStrings)

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
