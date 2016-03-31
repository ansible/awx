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
        listTitle: 'Jobs',

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
            /*
            id: {
                label: 'ID',
                key: true,
                noLink: true, //undocumented: 'key' above will automatically made the fields a link, but 'noLink' will override this setting
                desc: true,
                searchType: 'int',
                columnClass: 'col-xs-2 List-staticColumnAdjacent',
            },
            */
            name: {
                label: 'Name',
                columnClass: 'col-lg-4 col-md-4 col-sm-4 col-xs-6',
                defaultSearchField: true,
                linkTo: '/#/jobs/{{portal_job.id}}'
            },
            started: {
                label: 'Started',
                noLink: true,
                searchable: false,
                filter: "longDate",
                nosort: true,
                columnClass: "col-lg-4 col-md-4 col-sm-3 hidden-xs"
            }
        },

        actions: { }
    });
