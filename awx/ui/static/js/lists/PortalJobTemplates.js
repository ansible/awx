/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  PoralJobTemplates.js
 *  List view object for Job Templates data model.
 *
 *
 */

'use strict';

angular.module('PortalJobTemplatesListDefinition', [])
    .value('PortalJobTemplateList', {

        name: 'job_templates',
        iterator: 'job_template',
        // selectTitle: 'Add Job Template',
        editTitle: 'Job Templates',
        // selectInstructions: "Click on a row to select it, and click Finished when done. Use the <i class=\"icon-plus\"></i> " +
        //     "button to create a new job template.",
        index: false,
        hover: true,
        well: true,

        fields: {
            name: {
                label: 'Name',
                columnClass: 'col-lg-5 col-md-5 col-sm-9 col-xs-8'
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
