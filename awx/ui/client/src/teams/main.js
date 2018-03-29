/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import TeamsList from './list/teams-list.controller';
import TeamsAdd from './add/teams-add.controller';
import TeamsEdit from './edit/teams-edit.controller';
import TeamList from './teams.list';
import TeamForm from './teams.form';
import { N_ } from '../i18n';

export default
angular.module('Teams', [])
    .controller('TeamsList', TeamsList)
    .controller('TeamsAdd', TeamsAdd)
    .controller('TeamsEdit', TeamsEdit)
    .factory('TeamList', TeamList)
    .factory('TeamForm', TeamForm)
    .config(['$stateProvider', 'stateDefinitionsProvider',
        function($stateProvider, stateDefinitionsProvider) {
            let stateDefinitions = stateDefinitionsProvider.$get();

            // lazily generate a tree of substates which will replace this node in ui-router's stateRegistry
            // see: stateDefinition.factory for usage documentation
            $stateProvider.state({
                name: 'teams.**',
                url: '/teams',
                lazyLoad: () => stateDefinitions.generateTree({
                    parent: 'teams',
                    modes: ['add', 'edit'],
                    list: 'TeamList',
                    form: 'TeamForm',
                    controllers: {
                        list: TeamsList,
                        add: TeamsAdd,
                        edit: TeamsEdit
                    },
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'team'
                    },
                    resolve: {
                        edit: {
                            resolvedModels: ['MeModel', '$q', function(Me, $q) {
                                const promises = {
                                    me: new Me('get').then((me) => me.extend('get', 'admin_of_organizations'))
                                };

                                return $q.all(promises);
                            }]
                        },
                        list: {
                            resolvedModels: ['MeModel', '$q', function(Me, $q) {
                                const promises = {
                                    me: new Me('get')
                                };

                                return $q.all(promises);
                            }]
                        }
                    },
                    ncyBreadcrumb: {
                        label: N_('TEAMS')
                    }
                })
            });
        }
    ]);
