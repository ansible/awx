/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  PortalJobs.js
 *  List view object for portal job data model.
 *
 *  Used on dashboard to provide a list of all jobs, regardless of
 *  status.
 *
 */



export default
    angular.module('PortalJobsListDefinition', ['longDateFilter'])
    .value( 'PortalJobsList', {

        name: 'portal_jobs',
        iterator: 'portal_job',
        editTitle: 'Jobs',
        'class': 'table-condensed',
        index: false,
        hover: true,
        well: true,

        fields: {
            id: {
                label: 'ID',
                //ngClick:"viewJobLog(job.id)",
                key: true,
                noLink: true, //undocumented: 'key' above will automatically made the fields a link, but 'noLink' will override this setting
                desc: true,
                searchType: 'int',
                columnClass: 'col-lg-1 col-md-1 col-sm-2 col-xs-2',
                // awToolTip: "{{ job.status_tip }}",
                // awTipPlacement: "top",
            },
            status: {
                label: 'Status',
                columnClass: 'col-lg-1 col-md-2 col-sm-2 col-xs-2',
                // awToolTip: "{{ job.status_tip }}",
                // awTipPlacement: "top",
                dataTitle: "{{ portal_job.status_popover_title }}",
                icon: 'icon-job-{{ portal_job.status }}',
                iconOnly: true,
                // ngClick:"viewJobLog(job.id)",
                searchable: true,
                nosort: true,
                searchType: 'select',
                searchOptions: [
                    { name: "Success", value: "successful" },
                    { name: "Error", value: "error" },
                    { name: "Failed", value: "failed" },
                    { name: "Canceled", value: "canceled" }
                ]
            },
            started: {
                label: 'Started',
                noLink: true,
                searchable: false,
                filter: "longDate",
                columnClass: "col-lg-3 col-md-3 hidden-xs"
            },
            name: {
                label: 'Name',
                columnClass: 'col-md-5 col-xs-5',
                //ngClick: "viewJobLog(job.id, job.nameHref)",
                defaultSearchField: true
            }
        },

        actions: { },

        fieldActions: {
            job_details: {
                mode: 'all',
                ngClick: "viewJobLog(portal_job.id)",
                awToolTip: 'View job details',
                dataPlacement: 'top'
            }
        }
    });
