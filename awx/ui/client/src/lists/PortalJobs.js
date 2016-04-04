/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default
    angular.module('PortalJobsListDefinition', [])
    .value( 'PortalJobsList', {

        name: 'jobs',
        iterator: 'job',
        editTitle: 'Jobs',
        index: false,
        hover: true,
        well: true,
        listTitle: 'Jobs',

        fields: {
            status: {
                label: '',
                columnClass: 'List-staticColumn--smallStatus',
                dataTitle: "{{ job.status_popover_title }}",
                icon: 'icon-job-{{ job.status }}',
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
                key: true,
                label: 'Name',
                columnClass: 'col-lg-4 col-md-4 col-sm-4 col-xs-6',
                defaultSearchField: true,
                linkTo: '/#/jobs/{{job.id}}'
            },
            started: {
                label: 'Started',
                noLink: true,
                searchable: false,
                filter: "longDate",
                nosort: true,
                columnClass: "col-lg-4 col-md-4 col-sm-3"
            }
        },

        actions: { }
    });
