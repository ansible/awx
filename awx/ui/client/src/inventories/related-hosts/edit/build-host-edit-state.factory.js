/*************************************************
* Copyright (c) 2017 Ansible, Inc.
*
* All Rights Reserved
*************************************************/

import RelatedHostEditController from './host-edit.controller';

export default ['$stateExtender', 'templateUrl', '$injector',
    'RelatedHostsFormDefinition', 'NestedHostsFormDefinition',
    'nestedGroupListState',
    function($stateExtender, templateUrl, $injector,
        RelatedHostsFormDefinition, NestedHostsFormDefinition,
        nestedGroupListState){
        var val = function(field, formStateDefinition, params) {
            let state, states = [],
            list = field.include ? $injector.get(field.include) : field,
            breadcrumbLabel = (field.iterator.replace('_', ' ') + 's').toUpperCase(),
            stateConfig = {
                name: `${formStateDefinition.name}.${list.iterator}s.edit`,
                url: `/edit/:host_id`,
                ncyBreadcrumb: {
                    parent: `${formStateDefinition.name}`,
                    label: `${breadcrumbLabel}`
                },
                views: {
                    'hostForm@inventories': {
                        templateProvider: function(GenerateForm, RelatedHostsFormDefinition, NestedHostsFormDefinition, $stateParams) {
                            let form = RelatedHostsFormDefinition;
                            if($stateParams.group_id){
                                form = NestedHostsFormDefinition;
                            }
                            return GenerateForm.buildHTML(form, {
                                mode: 'edit',
                                related: false
                            });
                        },
                        controller: RelatedHostEditController
                    }
                },
                resolve: {
                    'FormDefinition': [params.form, function(definition) {
                        return definition;
                    }],
                    host: ['$stateParams', 'HostManageService', function($stateParams, HostManageService) {
                        return HostManageService.get({ id: $stateParams.host_id }).then(function(res) {
                            return res.data.results[0];
                        });
                    }]
                }
            };
            var relatedGroupListState;
            state = $stateExtender.buildDefinition(stateConfig);
            if(stateConfig.name === "inventories.edit.groups.edit.nested_hosts.edit"){
                relatedGroupListState = nestedGroupListState(NestedHostsFormDefinition.related.nested_groups, state, params);
                relatedGroupListState = $stateExtender.buildDefinition(relatedGroupListState);
                states.push(state, relatedGroupListState);
                return states;
            }
            if(stateConfig.name === "inventories.edit.hosts.edit"){
                relatedGroupListState = nestedGroupListState(RelatedHostsFormDefinition.related.nested_groups, state, params);
                relatedGroupListState = $stateExtender.buildDefinition(relatedGroupListState);
                states.push(state, relatedGroupListState);
                return states;
            }
            else {
                return state;
            }

        };
        return val;
    }
];
