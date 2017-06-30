export default ['i18n', function (i18n) {
    return {
        name: 'jobs',
        iterator: 'job',
        basePath: 'api/v2/instance_groups/{{$stateParams.instance_group_id}}/jobs/',
        index: false,
        hover: false,
        well: true,
        emptyListText: i18n._('No jobs have yet run.'),
        listTitle: false,

        fields: {
            status: {
                label: '',
                columnClass: 'col-lg-1 col-md-1 col-sm-2 col-xs-2 List-staticColumn--smallStatus',
                dataTipWatch: 'job.status_tip',
                awToolTip: "{{ job.status_tip }}",
                awTipPlacement: "right",
                dataTitle: "{{ job.status_popover_title }}",
                icon: 'icon-job-{{ job.status }}',
                iconOnly: true,
                ngClick: "viewjobResults(job)",
                nosort: true
            },
            id: {
                label: i18n._('ID'),
                ngClick: "viewjobResults(job)",
                columnClass: 'col-lg-1 col-md-1 col-sm-2 col-xs-2 List-staticColumnAdjacent',
                awToolTip: "{{ job.status_tip }}",
                dataPlacement: 'top',
                noLink: true
            },
            name: {
                label: i18n._('Name'),
                columnClass: 'col-lg-2 col-md-3 col-sm-4 col-xs-6',
                ngClick: "viewjobResults(job)",
                badgePlacement: 'right',
                badgeCustom: true,
                nosort: true,
                badgeIcon: `<a href="{{ job.workflow_result_link }}"
                    aw-tool-tip="{{'View workflow results'|translate}}"
                    data-placement="top"
                    data-original-title="" title="">
                    <i class="WorkflowBadge"
                        ng-show="job.launch_type === 'workflow' ">
                        W
                    </i>
                </a>`
            },
            type: {
                label: i18n._('Type'),
                ngBind: 'job.type_label',
                columnClass: "col-lg-2 hidden-md hidden-sm hidden-xs",
                nosort: true
            },
            finished: {
                label: i18n._('Finished'),
                noLink: true,
                filter: "longDate",
                columnClass: "col-lg-2 col-md-3 col-sm-3 hidden-xs",
                key: true,
                desc: true,
                nosort: true
            },
            labels: {
                label: i18n._('Labels'),
                type: 'labels',
                nosort: true,
                showDelete: false,
                columnClass: 'List-tableCell col-lg-4 col-md-4 hidden-sm hidden-xs',
                sourceModel: 'labels',
                sourceField: 'name'
            },
        }
    };
}];
