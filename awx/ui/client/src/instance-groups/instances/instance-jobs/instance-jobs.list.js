export default ['i18n', function(i18n) {
    return {

        name: 'instance_jobs',
        iterator: 'instance_job',
        index: false,
        hover: false,
        well: false,
        emptyListText: i18n._('No jobs have yet run.'),
        title: false,
        basePath: 'api/v2/instances/{{$stateParams.instance_id}}/jobs',

        fields: {
            status: {
                label: '',
                columnClass: 'col-lg-1 col-md-1 col-sm-2 col-xs-2 List-staticColumn--smallStatus',
                dataTipWatch: 'instance_job.status_tip',
                awToolTip: "{{ instance_job.status_tip }}",
                awTipPlacement: "right",
                dataTitle: "{{ instance_job.status_popover_title }}",
                icon: 'icon-job-{{ instance_job.status }}',
                iconOnly: true,
                ngClick:"viewjobResults(instance_job)",
                nosort: true
            },
            id: {
                label: i18n._('ID'),
                ngClick:"viewjobResults(instance_job)",
                columnClass: 'col-lg-1 col-md-1 col-sm-2 col-xs-2 List-staticColumnAdjacent',
                awToolTip: "{{ instance_job.status_tip }}",
                dataPlacement: 'top',
                noLink: true
            },
            name: {
                label: i18n._('Name'),
                columnClass: 'col-lg-2 col-md-3 col-sm-4 col-xs-6',
                ngClick: "viewjobResults(instance_job)",
                nosort: true,
                badgePlacement: 'right',
                badgeCustom: true,
                badgeIcon: `<a href="{{ instance_job.workflow_result_link }}"
                    aw-tool-tip="{{'View workflow results'|translate}}"
                    data-placement="top"
                    data-original-title="" title="">
                    <i class="WorkflowBadge"
                        ng-show="instance_job.launch_type === 'workflow' ">
                        W
                    </i>
                </a>`
            },
            type: {
                label: i18n._('Type'),
                ngBind: 'instance_job.type_label',
                link: false,
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
                sourceField: 'name',
            },
        }
    };
}];
