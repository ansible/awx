/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import { templateUrl } from '../shared/template-url/template-url.factory';
import OrganizationsList from './list/organizations-list.controller';
import OrganizationsAdd from './add/organizations-add.controller';
import OrganizationsEdit from './edit/organizations-edit.controller';
import organizationsLinkout from './linkout/main';
import OrganizationsLinkoutStates from './linkout/organizations-linkout.route';
import OrganizationForm from './organizations.form';
import OrganizationList from './organizations.list';
import { N_ } from '../i18n';


export default
angular.module('Organizations', [
        organizationsLinkout.name
    ])
    .controller('OrganizationsList', OrganizationsList)
    .controller('OrganizationsAdd', OrganizationsAdd)
    .controller('OrganizationsEdit', OrganizationsEdit)
    .factory('OrganizationForm', OrganizationForm)
    .factory('OrganizationList', OrganizationList)
    .config(['$stateProvider', 'stateDefinitionsProvider', '$stateExtenderProvider',
        function($stateProvider, stateDefinitionsProvider, $stateExtenderProvider) {
            let stateExtender = $stateExtenderProvider.$get(),
                stateDefinitions = stateDefinitionsProvider.$get();

            // lazily generate a tree of substates which will replace this node in ui-router's stateRegistry
            // see: stateDefinition.factory for usage documentation
            $stateProvider.state({
                name: 'organizations.**',
                url: '/organizations',
                lazyLoad: () => stateDefinitions.generateTree({
                    parent: 'organizations', // top-most node in the generated tree
                    modes: ['add', 'edit'], // form nodes to generate
                    list: 'OrganizationList',
                    form: 'OrganizationForm',
                    controllers: {
                        list: 'OrganizationsList',
                        add: 'OrganizationsAdd',
                        edit: 'OrganizationsEdit'
                    },
                    templates: {
                        list: templateUrl('organizations/list/organizations-list')
                    },
                    ncyBreadcrumb: {
                        label: N_('ORGANIZATIONS')
                    },
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'organization'
                    },
                    resolve: {
                        add: {
                            ConfigData: ['ConfigService', 'ProcessErrors', (ConfigService, ProcessErrors) => {
                                return ConfigService.getConfig()
                                    .then(response => response)
                                    .catch(({data, status}) => {
                                        ProcessErrors(null, data, status, null, {
                                            hdr: 'Error!',
                                            msg: 'Failed to get config. GET returned status: ' +
                                                'status: ' + status
                                        });
                                    });

                            }]
                        },
                        edit: {
                            ConfigData: ['ConfigService', 'ProcessErrors', (ConfigService, ProcessErrors) => {
                                return ConfigService.getConfig()
                                    .then(response => response)
                                    .catch(({data, status}) => {
                                        ProcessErrors(null, data, status, null, {
                                            hdr: 'Error!',
                                            msg: 'Failed to get config. GET returned status: ' +
                                                'status: ' + status
                                        });
                                    });
                            }],
                            InstanceGroupsData: ['$stateParams', 'Rest', 'GetBasePath', 'ProcessErrors',
                                function($stateParams, Rest, GetBasePath, ProcessErrors){
                                    let path = `${GetBasePath('organizations')}${$stateParams.organization_id}/instance_groups/`;
                                    Rest.setUrl(path);
                                    return Rest.get()
                                        .then(({data}) => {
                                            if (data.results.length > 0) {
                                                 return data.results;
                                            }
                                        })
                                        .catch(({data, status}) => {
                                            ProcessErrors(null, data, status, null, {
                                                hdr: 'Error!',
                                                msg: 'Failed to get instance groups. GET returned ' +
                                                    'status: ' + status
                                            });
                                    });
                                }]
                        }
                    }
                    // concat manually-defined state definitions with generated defintions
                }).then((generated) => {
                    let linkoutDefinitions = _.map(OrganizationsLinkoutStates, (state) => stateExtender.buildDefinition(state));
                    return {
                        states: _(generated.states)
                            .concat(linkoutDefinitions)
                            .value()
                    };
                })
            });
        }
    ]);
