/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Jobs.js
 *  List view object for job data model.
 *
 *  Used on dashboard to provide a list of all jobs, regardless of
 *  status.
 *
 */



export default
    angular.module('ScanJobsListDefinition', [])
    .value( 'ScanJobsList', {

        name: 'scan_job_templates',
        iterator: 'scan_job_template',
        editTitle: 'Scan Jobs',
        'class': 'table-condensed',
        index: false,
        hover: true,
        well: false,

        fields: {
            name: {
                key: true,
                label: 'Name',
                // columnClass: 'col-lg-5 col-md-5 col-sm-9 col-xs-8'
            },
            description: {
                label: 'Description',
                // columnClass: 'col-lg-4 col-md-3 hidden-sm hidden-xs'
            }
        },

        actions: {
            add: {
                mode: 'all', // One of: edit, select, all
                ngClick: 'addScanJobTemplate()',
                basePaths: ['job_templates'],
                awToolTip: 'Create a new template',
                ngHide: 'portalMode===true'
            },
            stream: {
                ngClick: "showActivity()",
                awToolTip: "View Activity Stream",
                icon: "icon-comments-alt",
                mode: 'edit',
                ngHide: 'portalMode===true',
                awFeature: 'activity_streams'
            }
        },

        fieldActions: {
            submit: {
                label: 'Launch',
                mode: 'all',
                ngClick: 'submitJob(job_template.id)',
                awToolTip: 'Start a job using this template',
                dataPlacement: 'top'
            },
            schedule: {
                label: 'Schedule',
                mode: 'all',
                ngHref: '#/job_templates/{{ job_template.id }}/schedules',
                awToolTip: 'Schedule future job template runs',
                dataPlacement: 'top',
            },
            edit: {
                label: 'Edit',
                ngClick: "editJobTemplate(job_template.id)",
                awToolTip: 'Edit template',
                "class": 'btn-default btn-xs',
                dataPlacement: 'top',
            },
            "delete": {
                label: 'Delete',
                ngClick: "deleteJobTemplate(job_template.id, job_template.name)",
                "class": 'btn-danger btn-xs',
                awToolTip: 'Delete template',
                dataPlacement: 'top',
            },
            copy: {
                label: 'Copy',
                ngClick: "copyJobTemplate(job_template.id, job_template.name)",
                "class": 'btn-danger btn-xs',
                awToolTip: 'Copy template',
                dataPlacement: 'top',
                ngHide: 'job_template.summary_fields.can_copy===false'

            }
        }
    });
