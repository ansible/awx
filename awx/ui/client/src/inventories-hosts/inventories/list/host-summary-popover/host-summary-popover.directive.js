export default ['templateUrl', 'Wait', '$filter', '$compile', 'i18n',
    function(templateUrl, Wait, $filter, $compile, i18n) {
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
                        elem.popover('destroy');
                    }
                    catch(err) {
                        //ignore
                    }
                    $('.popover').each(function() {
                        // remove lingering popover <div>. Seems to be a bug in TB3 RC1
                        $(this).remove();
                    });
                    $('.tooltip').each( function() {
                        // close any lingering tool tipss
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
                    var html, title = (scope.inventory.has_active_failures) ? "Recent Failed Jobs" : "Recent Successful Jobs";
                    Wait('stop');
                    if (data.count > 0) {
                        html = "<table class=\"table table-condensed flyout\" style=\"width: 100%\">\n";
                        html += "<thead>\n";
                        html += "<tr>";
                        html += "<th>" + i18n._("Status") + "</th>";
                        html += "<th>" + i18n._("Finished") + "</th>";
                        html += "<th>" + i18n._("Name") + "</th>";
                        html += "</tr>\n";
                        html += "</thead>\n";
                        html += "<tbody>\n";

                        data.results.forEach(function(row) {
                            if ((scope.inventory.has_active_failures && row.status === 'failed') || (!scope.inventory.has_active_failures && row.status === 'successful')) {
                                html += "<tr>\n";
                                html += "<td><a href=\"\" ng-click=\"viewJob(" + row.id + "," + "'" + row.type + "'" + ")\" " + "aw-tool-tip=\"" + row.status.charAt(0).toUpperCase() + row.status.slice(1) +
                                    ". Click for details\" aw-tip-placement=\"top\" data-tooltip-outer-class=\"Tooltip-secondary\"><i class=\"fa SmartStatus-tooltip--" + row.status + " icon-job-" + row.status + "\"></i></a></td>\n";
                                html += "<td>" + ($filter('longDate')(row.finished)) + "</td>";
                                html += "<td><a href=\"\" ng-click=\"viewJob(" + row.id + "," + "'" + row.type + "'" + ")\" " + "aw-tool-tip=\"" + row.status.charAt(0).toUpperCase() + row.status.slice(1) +
                                    ". Click for details\" aw-tip-placement=\"top\" data-tooltip-outer-class=\"Tooltip-secondary\">" + $filter('sanitize')(ellipsis(row.name)) + "</a></td>";
                                html += "</tr>\n";
                            }
                        });
                        html += "</tbody>\n";
                        html += "</table>\n";
                    }
                    else {
                        html = "<p>" + i18n._("No recent job data available for this inventory.") + "</p>\n";
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
