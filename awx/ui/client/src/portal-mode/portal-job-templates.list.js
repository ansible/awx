/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default ['i18n', function(i18n) {
    return {

        name: 'job_templates',
        iterator: 'job_template',
        editTitle: i18n._('JOB TEMPLATES'),
        listTitle: i18n._('JOB TEMPLATES'),
        index: false,
        hover: true,
        well: true,
        emptyListText: i18n._('There are no job templates to display at this time'),
        searchBarFullWidth: true,
        fields: {
            name: {
                key: true,
                label: i18n._('Name'),
                columnClass: 'col-lg-5 col-md-5 col-sm-9 col-xs-8',
                linkTo: '/#/templates/job_template/{{job_template.id}}',
                awToolTip: '{{job_template.description | sanitize}}',
                dataPlacement: 'top'
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
    };}];
