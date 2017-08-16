/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default ['i18n', function(i18n) {
    return {
        // These tooltip fields are consumed to build disabled related tabs tooltips in the form > add view
        awToolTip: i18n._('Please save and run a job to view.'),
        dataPlacement: 'top',
        name: 'completed_jobs',
        basePath: 'unified_jobs',
        iterator: 'completed_job',
        search: {
            "or__job__inventory": ''
        },
        editTitle: i18n._('COMPLETED JOBS'),
        index: false,
        hover: true,
        well: true,
        emptyListText: i18n._('No completed jobs'),

        fields: {
            status: {
                label: '',
                columnClass: 'List-staticColumn--smallStatus',
                awToolTip: "{{ completed_job.status_tip }}",
                awTipPlacement: "right",
                dataTitle: "{{ completed_job.status_popover_title }}",
                icon: 'icon-job-{{ completed_job.status }}',
                iconOnly: true,
                ngClick:"viewjobResults(completed_job)",
                nosort: true
            },
            id: {
                label: i18n._('ID'),
                ngClick:"viewjobResults(completed_job)",
                columnClass: 'col-lg-1 col-md-1 col-sm-2 col-xs-2 List-staticColumnAdjacent',
                awToolTip: "{{ completed_job.status_tip }}",
                dataPlacement: 'top'
            },
            name: {
                label: i18n._('Name'),
                columnClass: 'col-lg-4 col-md-4 col-sm-4 col-xs-6',
                ngClick: "viewjobResults(completed_job)",
                awToolTip: "{{ completed_job.name | sanitize }}",
                dataPlacement: 'top'
            },
            type: {
                label: i18n._('Type'),
                ngBind: 'completed_job.type_label',
                link: false,
                columnClass: "col-lg-2 col-md-2 hidden-sm hidden-xs",
            },
            finished: {
                label: i18n._('Finished'),
                noLink: true,
                filter: "longDate",
                columnClass: "col-lg-3 col-md-3 col-sm-3 hidden-xs",
                key: true,
                desc: true
            }
        },

        actions: { },

        fieldActions: {

            columnClass: 'col-lg-2 col-md-2 col-sm-3 col-xs-4',

            submit: {
                icon: 'icon-rocket',
                mode: 'all',
                ngClick: 'relaunchJob($event, completed_job.id)',
                awToolTip: i18n._('Relaunch using the same parameters'),
                dataPlacement: 'top',
                ngShow: "!completed_job.type == 'system_job' || completed_job.summary_fields.user_capabilities.start"
            },
            "delete": {
                mode: 'all',
                ngClick: 'deleteJob(completed_job.id)',
                awToolTip: i18n._('Delete the job'),
                dataPlacement: 'top',
                ngShow: 'completed_job.summary_fields.user_capabilities.delete'
            }
        }
    };}];
