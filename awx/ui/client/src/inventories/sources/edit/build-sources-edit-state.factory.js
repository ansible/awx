/*************************************************
* Copyright (c) 2017 Ansible, Inc.
*
* All Rights Reserved
*************************************************/

import SourcesEditController from './sources-edit.controller';

export default ['$stateExtender', 'templateUrl', '$injector',
    function($stateExtender, templateUrl, $injector){
        var val = function(field, formStateDefinition, params) {
            let state,
            list = field.include ? $injector.get(field.include) : field,
            breadcrumbLabel = (field.iterator.replace('_', ' ') + 's').toUpperCase(),
            stateConfig = {
                name: `${formStateDefinition.name}.${list.iterator}s.edit`,
                url: `/edit/:source_id`,
                ncyBreadcrumb: {
                    parent: `${formStateDefinition.name}`,
                    label: `${breadcrumbLabel}`
                },
                views: {
                    'groupForm@inventories': {
                        templateProvider: function(GenerateForm, SourcesFormDefinition) {
                            let form = SourcesFormDefinition;
                            return GenerateForm.buildHTML(form, {
                                mode: 'edit',
                                related: false
                            });
                        },
                        controller: SourcesEditController
                    }
                },
                resolve: {
                    'FormDefinition': [params.form, function(definition) {
                        return definition;
                    }],
                    inventorySourceData: ['$stateParams', 'SourcesService', function($stateParams, SourcesService) {
                        return SourcesService.get({id: $stateParams.source_id }).then(res => res.data.results[0]);
                    }]
                }
            };

            state = $stateExtender.buildDefinition(stateConfig);
            return state;
        };
        return val;
    }
];
