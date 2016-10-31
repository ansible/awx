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


export default
angular.module('Organizations', [
        organizationsLinkout.name
    ])
    .controller('OrganizationsList', OrganizationsList)
    .controller('OrganizationsAdd', OrganizationsAdd)
    .controller('OrganizationsEdit', OrganizationsEdit)
    .config(['$stateProvider', 'stateDefinitionsProvider', '$stateExtenderProvider',
        function($stateProvider, stateDefinitionsProvider, $stateExtenderProvider) {
            let stateExtender = $stateExtenderProvider.$get(),
                stateDefinitions = stateDefinitionsProvider.$get();

            // lazily generate a tree of substates which will replace this node in ui-router's stateRegistry
            // see: stateDefinition.factory for usage documentation
            $stateProvider.state({
                name: 'organizations',
                url: '/organizations',
                data: {
                    activityStream: true,
                    activityStreamTarget: 'organization'
                },
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
                        parent: 'setup',
                        label: 'ORGANIZATIONS'
                    },
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
