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
import galaxyCredentialsMultiselect from './galaxy-credentials-multiselect/galaxy-credentials.directive';
import galaxyCredentialsModal from './galaxy-credentials-multiselect/galaxy-credentials-modal/galaxy-credentials-modal.directive';

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
    .directive('galaxyCredentialsMultiselect', galaxyCredentialsMultiselect)
    .directive('galaxyCredentialsModal', galaxyCredentialsModal)
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

                            }],
                            defaultGalaxyCredential: ['Rest', 'GetBasePath', 'ProcessErrors',
                                function(Rest, GetBasePath, ProcessErrors){
                                    Rest.setUrl(GetBasePath('credentials'));
                                    return Rest.get({
                                        params: {
                                            credential_type__kind: 'galaxy',
                                            managed_by_tower: true
                                        }
                                    })
                                    .then(({data}) => {
                                        if (data.results.length > 0) {
                                            return data.results;
                                        }
                                    })
                                    .catch(({data, status}) => {
                                        ProcessErrors(null, data, status, null, {
                                            hdr: 'Error!',
                                            msg: 'Failed to get default Galaxy credential. GET returned ' +
                                                'status: ' + status
                                        });
                                    });
                            }],
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
                            GalaxyCredentialsData: ['$stateParams', 'Rest', 'GetBasePath', 'ProcessErrors',
                                function($stateParams, Rest, GetBasePath, ProcessErrors){
                                    let path = `${GetBasePath('organizations')}${$stateParams.organization_id}/galaxy_credentials/`;
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
                                                msg: 'Failed to get credentials. GET returned ' +
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
                            }],
                            isOrgAuditor: ['Rest', 'ProcessErrors', 'GetBasePath', 'i18n', '$stateParams',
                                function(Rest, ProcessErrors, GetBasePath, i18n, $stateParams) {
                                    Rest.setUrl(`${GetBasePath('organizations')}?role_level=auditor_role&id=${$stateParams.organization_id}`);
                                    return Rest.get()
                                        .then(({data}) => {
                                            return data.count > 0;
                                        })
                                        .catch(({data, status}) => {
                                            ProcessErrors(null, data, status, null, {
                                                hdr: i18n._('Error!'),
                                                msg: i18n._('Failed while checking to see if user is a notification administrator of this organization. GET returned ') + status
                                            });
                                    });
                            }],
                            isOrgAdmin: ['ProcessErrors', 'i18n', '$stateParams', 'OrgAdminLookup',
                                function(ProcessErrors, i18n, $stateParams, OrgAdminLookup) {
                                    return OrgAdminLookup.checkForAdminAccess({organization: $stateParams.organization_id})
                                    .then(function(isOrgAdmin){
                                        return isOrgAdmin;
                                    })
                                    .catch(({data, status}) => {
                                        ProcessErrors(null, data, status, null, {
                                            hdr: i18n._('Error!'),
                                            msg: i18n._('Failed while checking to see if user is an administrator of this organization. GET returned ') + status
                                        });
                                    });
                                    
                            }],
                            isNotificationAdmin: ['Rest', 'ProcessErrors', 'GetBasePath', 'i18n',
                                function(Rest, ProcessErrors, GetBasePath, i18n) {
                                    Rest.setUrl(`${GetBasePath('organizations')}?role_level=notification_admin_role&page_size=1`);
                                    return Rest.get()
                                        .then(({data}) => {
                                            return data.count > 0;
                                        })
                                        .catch(({data, status}) => {
                                            ProcessErrors(null, data, status, null, {
                                                hdr: i18n._('Error!'),
                                                msg: i18n._('Failed to get organizations for which this user is a notification admin. GET returned ') + status
                                            });
                                    });
                            }],
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
