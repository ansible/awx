/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import hostEdit from './edit/main';
 import hostList from './list/main';
 import HostsList from './host.list';
 import HostsForm from './host.form';
 import { templateUrl } from '../../shared/template-url/template-url.factory';
 import { N_ } from '../../i18n';
 import ansibleFactsRoute from '../shared/ansible-facts/ansible-facts.route';
 import insightsRoute from '../inventories/insights/insights.route';
 import hostGroupsRoute from './related/groups/hosts-related-groups.route';
 import hostGroupsAssociateRoute from './related/groups/hosts-related-groups-associate.route';
 import hostCompletedJobsRoute from '~features/jobs/routes/hostCompletedJobs.route.js';
 import hostGroups from './related/groups/main';

export default
angular.module('host', [
        hostEdit.name,
        hostList.name,
        hostGroups.name
    ])
    .factory('HostsForm', HostsForm)
    .factory('HostsList', HostsList)
    .config(['$stateProvider', 'stateDefinitionsProvider', '$stateExtenderProvider',
        function($stateProvider, stateDefinitionsProvider, $stateExtenderProvider) {
            let stateDefinitions = stateDefinitionsProvider.$get(),
            stateExtender = $stateExtenderProvider.$get();

            let generateHostStates = function(){
                let hostTree = stateDefinitions.generateTree({
                    parent: 'hosts', // top-most node in the generated tree (will replace this state definition)
                    modes: ['edit'],
                    list: 'HostsList',
                    form: 'HostsForm',
                    controllers: {
                        edit: 'HostEditController'
                    },
                    breadcrumbs: {
                        edit: '{{breadcrumb.host_name}}'
                    },
                    urls: {
                        list: '/hosts'
                    },
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'host'
                    },
                    resolve: {
                        edit: {
                            host: ['Rest', '$stateParams', 'GetBasePath',
                                function(Rest, $stateParams, GetBasePath) {
                                    let path = GetBasePath('hosts') + $stateParams.host_id;
                                    Rest.setUrl(path);
                                    return Rest.get();
                                }
                            ]
                        },
                        list: {
                            canAdd: ['rbacUiControlService', function(rbacUiControlService) {
                                return rbacUiControlService.canAdd('hosts')
                                    .then(function(res) {
                                        return res.canAdd;
                                    })
                                    .catch(function() {
                                        return false;
                                    });
                            }]
                        }
                    },
                    views: {
                        '@': {
                            templateUrl: templateUrl('inventories-hosts/hosts/hosts'),
                            controller: 'HostListController'
                        }
                    },
                    ncyBreadcrumb: {
                        label: N_('HOSTS')
                    }
                });

                let hostAnsibleFacts = _.cloneDeep(ansibleFactsRoute);
                hostAnsibleFacts.name = 'hosts.edit.ansible_facts';

                let hostInsights = _.cloneDeep(insightsRoute);
                hostInsights.name = 'hosts.edit.insights';

                let hostCompletedJobs = _.cloneDeep(hostCompletedJobsRoute);
                hostCompletedJobs.name = 'hosts.edit.completed_jobs';

                return Promise.all([
                    hostTree
                ]).then((generated) => {
                    return {
                        states: _.reduce(generated, (result, definition) => {
                            return result.concat(definition.states);
                        }, [
                            stateExtender.buildDefinition(hostAnsibleFacts),
                            stateExtender.buildDefinition(hostInsights),
                            stateExtender.buildDefinition(hostGroupsRoute),
                            stateExtender.buildDefinition(hostGroupsAssociateRoute),
                            stateExtender.buildDefinition(hostCompletedJobs)
                        ])
                    };
                });
            };

            $stateProvider.state({
                name: 'hosts.**',
                url: '/hosts',
                lazyLoad: () => generateHostStates()
            });
        }
    ]);
