/*************************************************
* Copyright (c) 2017 Ansible, Inc.
*
* All Rights Reserved
*************************************************/

import GroupAddController from '../add/groups-add.controller';

export default ['$stateExtender', 'templateUrl', '$injector',
    function($stateExtender, templateUrl, $injector){
        var val = function(field, formStateDefinition, params) {
            let state,
            list = field.include ? $injector.get(field.include) : field,
            breadcrumbLabel = (field.iterator.replace('_', ' ') + 's').toUpperCase(),
            stateConfig = {
                name: `${formStateDefinition.name}.${list.iterator}s.add`,
                url: `/add`,
                ncyBreadcrumb: {
                    parent: `${formStateDefinition.name}`,
                    label: `${breadcrumbLabel}`
                },
                views: {
                    'nestedGroupForm@inventories': {
                        templateProvider: function(GenerateForm, GroupForm) {
                            let form = GroupForm;
                            return GenerateForm.buildHTML(form, {
                                mode: 'add',
                                related: false
                            });
                        },
                        controller: GroupAddController
                    }
                },
                resolve: {
                    'FormDefinition': [params.form, function(definition) {
                        return definition;
                    }]
                }
            };

            state = $stateExtender.buildDefinition(stateConfig);
            return state;
        };
        return val;
    }
];
