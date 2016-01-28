/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default
    angular.module('PortalJobsListDefinition', [])
    .value( 'PortalJobsList', {

        name: 'portal_jobs',
        iterator: 'portal_job',
        editTitle: 'Jobs',
        'class': 'table-condensed',
        index: false,
        hover: true,
        well: true,

        fields: {
            status: {
                label: '',
                columnClass: 'List-staticColumn--smallStatus',
                dataTitle: "{{ portal_job.status_popover_title }}",
                icon: 'icon-job-{{ portal_job.status }}',
                iconOnly: true,
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
            id: {
                label: 'ID',
                key: true,
                noLink: true, //undocumented: 'key' above will automatically made the fields a link, but 'noLink' will override this setting
                desc: true,
                searchType: 'int',
                columnClass: 'col-lg-1 col-md-1 col-sm-2 col-xs-2 List-staticColumnAdjacent',
            },
            name: {
                label: 'Name',
                columnClass: 'col-lg-4 col-md-4 col-sm-4 col-xs-6',
                defaultSearchField: true
            },
            started: {
                label: 'Started',
                noLink: true,
                searchable: false,
                filter: "longDate",
                columnClass: "col-lg-4 col-md-4 col-sm-3 xs-hidden"
            }
        },

        actions: { },

        fieldActions: {

            columnClass: 'col-lg-3 col-md-4 col-sm-3 col-xs-4',

            job_details: {
                mode: 'all',
                ngClick: "viewJobLog(portal_job.id)",
                awToolTip: 'View job details',
                dataPlacement: 'top'
            }
        }
    });
