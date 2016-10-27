/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default
    angular.module('PortalJobsListDefinition', [])
    .factory('PortalJobsList', ['i18n', function(i18n) {
    return {

        name: 'jobs',
        iterator: 'job',
        editTitle: i18n._('Jobs'),
        index: false,
        hover: true,
        well: true,
        listTitle: i18n._('Jobs'),
        emptyListText: i18n._('There are no jobs to display at this time'),

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
                label: i18n._('Name'),
                columnClass: 'col-lg-4 col-md-4 col-sm-4 col-xs-6 List-staticColumnAdjacent',
                defaultSearchField: true,
                linkTo: '/#/jobs/{{job.id}}',
                searchDefault: true
            },
            finished: {
                label: i18n._('Finished'),
                noLink: true,
                searchable: false,
                filter: "longDate",
                key: true,
                desc: true,
                columnClass: "col-lg-4 col-md-4 col-sm-3"
            }
        },

        actions: { }
    };}]);
