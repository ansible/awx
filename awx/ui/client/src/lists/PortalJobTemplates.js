/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default
    angular.module('PortalJobTemplatesListDefinition', [])
    .factory('PortalJobTemplateList', ['i18n', function(i18n) {
    return {

        name: 'job_templates',
        iterator: 'job_template',
        editTitle: i18n._('Job Templates'),
        listTitle: i18n._('Job Templates'),
        index: false,
        hover: true,
        well: true,
        emptyListText: i18n._('There are no job templates to display at this time'),
        fields: {
            name: {
                key: true,
                label: i18n._('Name'),
                columnClass: 'col-lg-5 col-md-5 col-sm-9 col-xs-8',
                linkTo: '/#/job_templates/{{job_template.id}}',
            },
            description: {
                label: i18n._('Description'),
                columnClass: 'col-lg-4 col-md-4 hidden-sm hidden-xs'
            }
        },

        actions: {
        },

        fieldActions: {
            submit: {
                label: i18n._('Launch'),
                mode: 'all',
                ngClick: 'submitJob(job_template.id)',
                awToolTip: i18n._('Start a job using this template'),
                dataPlacement: 'top'
            }
        }
    };}]);
