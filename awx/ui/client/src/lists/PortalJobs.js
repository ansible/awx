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
        emptyListText: 'There are no jobs to display at this time',

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
                label: 'Name',
                columnClass: 'col-lg-4 col-md-4 col-sm-4 col-xs-6 List-staticColumnAdjacent',
                defaultSearchField: true,
                linkTo: '/#/jobs/{{job.id}}'
            },
            finished: {
                label: 'Finished',
                noLink: true,
                searchable: false,
                filter: "longDate",
                key: true,
                columnClass: "col-lg-4 col-md-4 col-sm-3"
            }
        },

        actions: { }
    });
