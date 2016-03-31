/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 

export default
    angular.module('PortalJobTemplatesListDefinition', [])
    .value('PortalJobTemplateList', {

        name: 'job_templates',
        iterator: 'job_template',
        // selectTitle: 'Add Job Template',
        editTitle: 'Job Templates',
        listTitle: 'Job Templates',
        // selectInstructions: "Click on a row to select it, and click Finished when done. Use the <i class=\"icon-plus\"></i> " +
        //     "button to create a new job template.",
        index: false,
        hover: true,
        well: true,

        fields: {
            name: {
                key: true,
                label: 'Name',
                columnClass: 'col-lg-5 col-md-5 col-sm-9 col-xs-8',
                linkTo: '/#/job_templates/{{job_template.id}}'
            },
            description: {
                label: 'Description',
                columnClass: 'col-lg-4 col-md-4 hidden-sm hidden-xs'
            }
        },

        actions: {
        },

        fieldActions: {
            submit: {
                label: 'Launch',
                mode: 'all',
                ngClick: 'submitJob(job_template.id)',
                awToolTip: 'Start a job using this template',
                dataPlacement: 'top'
            }
        }
    });
