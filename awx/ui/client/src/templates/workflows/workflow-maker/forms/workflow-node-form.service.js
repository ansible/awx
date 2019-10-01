/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['TemplateList', 'ProjectList', 'InventorySourcesList', 'i18n',
    function(TemplateList, ProjectList, InventorySourcesList, i18n){
        return {
            inventorySourceListDefinition: function() {
                const inventorySourceList = _.cloneDeep(InventorySourcesList);
                inventorySourceList.name = 'wf_maker_inventory_sources';
                inventorySourceList.iterator = 'wf_maker_inventory_source';
                inventorySourceList.maxVisiblePages = 5;
                inventorySourceList.searchBarFullWidth = true;
                inventorySourceList.disableRow = "{{ readOnly }}";
                inventorySourceList.disableRowValue = 'readOnly';

                return inventorySourceList;
            },
            projectListDefinition: function(){
                const projectList = _.cloneDeep(ProjectList);
                delete projectList.fields.status;
                delete projectList.fields.scm_type;
                delete projectList.fields.last_updated;
                projectList.name = 'wf_maker_projects';
                projectList.iterator = 'wf_maker_project';
                projectList.fields.name.columnClass = "col-md-11";
                projectList.maxVisiblePages = 5;
                projectList.searchBarFullWidth = true;
                projectList.disableRow = "{{ readOnly }}";
                projectList.disableRowValue = 'readOnly';

                return projectList;
            },
            templateListDefinition: function(){
                const templateList = _.cloneDeep(TemplateList);
                delete templateList.actions;
                delete templateList.fields.type;
                delete templateList.fields.description;
                delete templateList.fields.smart_status;
                delete templateList.fields.labels;
                delete templateList.fieldActions;
                templateList.name = 'wf_maker_templates';
                templateList.iterator = 'wf_maker_template';
                templateList.fields.name.columnClass = "col-md-8";
                templateList.fields.name.tag = i18n._('WORKFLOW');
                templateList.fields.name.showTag = "{{wf_maker_template.type === 'workflow_job_template'}}";
                templateList.disableRow = "{{ readOnly }}";
                templateList.disableRowValue = 'readOnly';
                templateList.basePath = 'unified_job_templates';
                templateList.fields.info = {
                    ngInclude: "'/static/partials/job-template-details.html'",
                    type: 'template',
                    columnClass: 'col-md-3',
                    infoHeaderClass: 'col-md-3',
                    label: '',
                    nosort: true
                };
                templateList.maxVisiblePages = 5;
                templateList.searchBarFullWidth = true;

                return templateList;
            }
        };
    }
];
