/*************************************************
* Copyright (c) 2017 Ansible, Inc.
*
* All Rights Reserved
*************************************************/

import GroupEditController from './groups-edit.controller';

export default ['$stateExtender', 'templateUrl', '$injector',
    'stateDefinitions','GroupForm','nestedGroupListState',
    'nestedHostsListState', 'buildHostAddState', 'buildHostEditState',
    'nestedGroupAddState',
    function($stateExtender, templateUrl, $injector, stateDefinitions, GroupForm,
        nestedGroupListState, nestedHostsListState, buildHostAddState,
        buildHostEditState, nestedGroupAddState){
        var val = function(field, formStateDefinition, params) {
            let state, states = [],
            list = field.include ? $injector.get(field.include) : field,
            breadcrumbLabel = (field.iterator.replace('_', ' ') + 's').toUpperCase(),
            stateConfig = {
                name: `${formStateDefinition.name}.${list.iterator}s.edit`,
                url: `/edit/:group_id`,
                ncyBreadcrumb: {
                    parent: `${formStateDefinition.name}`,
                    label: `${breadcrumbLabel}`
                },
                views: {
                    'groupForm@inventories': {
                        templateProvider: function(GenerateForm, GroupForm) {
                            let form = GroupForm;
                            return GenerateForm.buildHTML(form, {
                                mode: 'edit',
                                related: false
                            });
                        },
                        controller: GroupEditController
                    }
                },
                resolve: {
                    'FormDefinition': [params.form, function(definition) {
                        return definition;
                    }],
                    groupData: ['$stateParams', 'GroupManageService', function($stateParams, GroupManageService) {
                        return GroupManageService.get({ id: $stateParams.group_id }).then(res => res.data.results[0]);
                    }]
                }
            };
            state = $stateExtender.buildDefinition(stateConfig);

            let relatedGroupListState = nestedGroupListState(GroupForm.related.nested_groups, state, params);
            let relatedGroupsAddState = nestedGroupAddState(GroupForm.related.nested_groups, state, params);
            relatedGroupListState = $stateExtender.buildDefinition(relatedGroupListState);
            relatedGroupsAddState = $stateExtender.buildDefinition(relatedGroupsAddState);

            let relatedHostsListState = nestedHostsListState(GroupForm.related.nested_hosts, state, params);
            let relatedHostsAddState = buildHostAddState(GroupForm.related.nested_hosts, state, params);
            let relatedHostsEditState = buildHostEditState(GroupForm.related.nested_hosts, state, params);
            relatedHostsListState = $stateExtender.buildDefinition(relatedHostsListState);
            relatedHostsAddState = $stateExtender.buildDefinition(relatedHostsAddState);
            if(Array.isArray(relatedHostsEditState))
            {
                relatedHostsEditState[0] = $stateExtender.buildDefinition(relatedHostsEditState[0]);
                relatedHostsEditState[1] = $stateExtender.buildDefinition(relatedHostsEditState[1]);
                states.push(state,
                    relatedGroupListState,
                    relatedGroupsAddState,
                    relatedHostsListState,
                    relatedHostsAddState,
                    relatedHostsEditState[0],
                    relatedHostsEditState[1]);
            }
            else {
                relatedHostsEditState = $stateExtender.buildDefinition(relatedHostsEditState);
                states.push(state,
                    relatedGroupListState,
                    relatedGroupsAddState,
                    relatedHostsListState,
                    relatedHostsAddState,
                    relatedHostsEditState);
            }

            // states.push(state,
            //     relatedGroupListState,
            //     relatedGroupsAddState,
            //     relatedHostsListState,
            //     relatedHostsAddState,
            //     relatedHostsEditState[0],
            //     relatedHostsEditState[1]);
            return states;
        };
        return val;
    }
];
