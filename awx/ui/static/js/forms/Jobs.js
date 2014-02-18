/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Jobs.js
 *  Form definition for Jobs model
 *
 *  @dict
 */
angular.module('JobFormDefinition', [])
    .value('JobForm', {

        addTitle: 'Create Job',
        editTitle: '{{ id }} - {{ name }}',
        name: 'jobs',
        well: true,
        base: 'jobs',
        collapse: true,
        collapseMode: 'edit',
        collapseTitle: 'Job Status',
        collapseOpenFirst: true,   //Always open first panel
        
        navigationLinks: {
            details: {
                href: "/#/jobs/{{ job_id }}",
                label: 'Status',
                icon: 'icon-zoom-in',
                active: true,
                ngShow: "job_id !== null"
            },
            events: {
                href: "/#/jobs/{{ job_id }}/job_events",
                label: 'Events',
                icon: 'icon-list-ul'
            },
            hosts: {
                href: "/#/jobs/{{ job_id }}/job_host_summaries",
                label: 'Host Summary',
                icon: 'icon-laptop'
            }
        },

        fields: {
            status: {
                type: 'custom',
                control: "<div class=\"job-detail-status\"><span style=\"padding-right: 15px; font-weight: bold;\">Status</span> " +
                    "<i class=\"fa icon-job-{{ status }}\"></i> {{ status }}</div>",
                readonly: true
            },
            created: {
                label: 'Created On',
                type: 'text',
                readonly: true
            },
            result_stdout: {
                label: 'Standard Out',
                type: 'textarea',
                readonly: true,
                xtraWide: true,
                rows: "{{ stdout_rows }}",
                "class": 'nowrap mono-space',
                ngShow: "result_stdout != ''"
            },
            result_traceback: {
                label: 'Traceback',
                type: 'textarea',
                xtraWide: true,
                readonly: true,
                rows: "{{ traceback_rows }}",
                "class": 'nowrap mono-space',
                ngShow: "result_traceback != ''"
            }
        },

        actions: {
            refresh: {
                dataPlacement: 'top',
                icon: "icon-refresh",
                iconSize: 'large',
                mode: 'all',
                //ngShow: "job_status == 'pending' || job_status == 'waiting' || job_status == 'running'",
                'class': 'btn-xs btn-primary',
                awToolTip: "Refresh the page",
                ngClick: "refresh()"
            }
        },

        related: {
            job_template:  {
                type: 'collection',
                title: 'Job Tempate',
                iterator: 'job',
                index: false,
                open: false,
                
                fields: { }
            }
        }
    });