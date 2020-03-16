export default ['templateUrl', 'Wait', '$filter', '$compile', 'i18n', '$log',
    function(templateUrl, Wait, $filter, $compile, i18n, $log) {
        return {
            restrict: 'E',
            replace: false,
            scope: {
                inventory: '='
            },
            controller: 'HostSummaryPopoverController',
            templateUrl: templateUrl('inventories-hosts/inventories/list/host-summary-popover/host-summary-popover'),
            link: function(scope) {

                function ellipsis(a) {
                    if (a.length > 20) {
                        return a.substr(0,20) + '...';
                    }
                    return a;
                }

                function attachElem(event, html, title) {
                    var elem = $(event.target).parent();

                    try {
                        elem.tooltip('hide');
                        elem.popover('dispose');
                    }
                    catch(err) {
                        $log.debug(err);
                    }
                    $('.popover').each(function() {
                        // remove lingering popover <div>. Seems to be a bug in TB3 RC1
                        $(this).remove();
                    });
                    $('.tooltip').each( function() {
                        // close any lingering tooltips
                        $(this).hide();
                    });
                    elem.attr({
                        "aw-pop-over": html,
                        "data-popover-title": title,
                        "data-placement": "right" });
                    elem.removeAttr('ng-click');
                    $compile(elem)(scope);
                    scope.triggerPopover(event);
                }

                scope.generateTable = function(data, event){
                    var html, title = (scope.inventory.has_active_failures) ? i18n._("Recent Failed Jobs") : i18n._("Recent Successful Jobs");
                    Wait('stop');
                    if (data.count > 0) {
                        html = `
                            <table class="table table-condensed flyout" style="width: 100%">
                                <thead>
                                    <tr>
                                        <th>${i18n._("Status")}</th>
                                        <th>${i18n._("Finished")}</th>
                                        <th>${i18n._("Name")}</th>
                                    </tr>
                                </thead>
                                <tbody>
                        `;

                        data.results.forEach(function(row) {
                            let href = '';
                            switch (row.type) {
                                case 'job':
                                case 'ad_hoc_command':
                                case 'system_job':
                                case 'project_update':
                                case 'inventory_update':
                                    href = `#/jobs/${row.id}`;
                                    break;
                                case 'workflow_job':
                                    href = `#/workflows/${row.id}`;
                                    break;
                                default:
                                    break;
                            }
                            if ((scope.inventory.has_active_failures && row.status === 'failed') || (!scope.inventory.has_active_failures && row.status === 'successful')) {
                                html += `
                                    <tr>
                                        <td>
                                            <a href="${href}" aria-label="{{'View job' | translate}}">
                                                <i class="fa SmartStatus-tooltip--${row.status} icon-job-${row.status}"></i>
                                            </a>
                                        </td>
                                        <td>${($filter('longDate')(row.finished))}</td>
                                        <td>
                                            <a href="${href}">${$filter('sanitize')(ellipsis(row.name))}</a>
                                        </td>
                                    </tr>
                                `;
                            }
                        });
                        html += `</tbody></table>`;
                    }
                    else {
                        html = `<p>${i18n._("No recent job data available for this inventory.")}</p>`;
                    }

                    attachElem(event, html, title);
                };

                scope.showHostSummary = function(event) {
                    try{
                        var elem = $(event.target).parent();
                        // if the popover is visible already, then exit the function here
                        if(elem.data()['bs.popover'].tip().hasClass('in')){
                            return;
                        }
                    }
                    catch(err){
                        scope.gatherRecentJobs(event);
                    }
                };

            }
        };
    }
];
