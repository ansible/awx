/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default ['i18n', function(i18n) {
    return {

        name: 'jobs',
        iterator: 'job',
        editTitle: i18n._('JOBS'),
        index: false,
        hover: true,
        well: true,
        listTitle: i18n._('JOBS'),
        emptyListText: i18n._('There are no jobs to display at this time'),
        searchBarFullWidth: true,

        fields: {
            status: {
                label: '',
                columnClass: 'List-staticColumn--smallStatus',
                dataTitle: "{{ job.status_popover_title }}",
                icon: 'icon-job-{{ job.status }}',
                iconOnly: true,
                nosort: true,
                awTipPlacement: "top",
                awToolTip: "{{ job.status_tip }}",
                dataTipWatch: 'job.status_tip',
                ngClick:"viewjobResults(job)",
            },
            name: {
                label: i18n._('Name'),
                columnClass: 'col-lg-4 col-md-4 col-sm-4 col-xs-6 List-staticColumnAdjacent',
                linkTo: '/#/jobs/{{job.id}}',
            },
            finished: {
                label: i18n._('Finished'),
                noLink: true,
                filter: "longDate",
                key: true,
                desc: true,
                columnClass: "col-lg-4 col-md-4 col-sm-3"
            }
        },

        actions: { }
    };}];
