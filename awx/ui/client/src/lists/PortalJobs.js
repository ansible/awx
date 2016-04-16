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
        searchSize: 'col-lg-8 col-md-8 col-sm-12 col-xs-12',

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
                searchOptions: [],
                searchLabel: 'Status'
            },
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
