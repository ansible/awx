export default ['templateUrl', '$compile', 'Wait', '$filter',
    function(templateUrl, $compile, Wait, $filter) {
        return {
            restrict: 'E',
            replace: false,
            scope: {
                inventory: '='
            },
            controller: 'SourceSummaryPopoverController',
            templateUrl: templateUrl('inventories/list/source-summary-popover/source-summary-popover'),
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

                scope.generateTable = function(data, event) {
                    var html, title;

                    Wait('stop');

                    // Build the html for our popover
                    html = "<table class=\"table table-condensed flyout\" style=\"width: 100%\">\n";
                    html += "<thead>\n";
                    html += "<tr>";
                    html += "<th>Status</th>";
                    html += "<th>Last Sync</th>";
                    html += "<th>Source</th>";
                    html += "</tr>";
                    html += "</thead>\n";
                    html += "<tbody>\n";
                    data.results.forEach( function(row) {
                        if (row.related.last_update) {
                            html += "<tr>";
                            html += `<td><a href="" ng-click="viewJob('${row.related.last_update}')" aw-tool-tip="${row.status.charAt(0).toUpperCase() + row.status.slice(1)}. Click for details" aw-tip-placement="top"><i class="SmartStatus-tooltip--${row.status} fa icon-job-${row.status}"></i></a></td>`;
                            html += "<td>" + ($filter('longDate')(row.last_updated)) + "</td>";
                            html += "<td><a href=\"\" ng-click=\"viewJob('" + row.related.last_update + "')\">" + $filter('sanitize')(ellipsis(row.name)) + "</a></td>";
                            html += "</tr>\n";
                        }
                        else {
                            html += "<tr>";
                            html += "<td><a href=\"\" aw-tool-tip=\"No sync data\" aw-tip-placement=\"top\"><i class=\"fa icon-job-none\"></i></a></td>";
                            html += "<td>NA</td>";
                            html += "<td><a href=\"\">" + $filter('sanitize')(ellipsis(row.name)) + "</a></td>";
                            html += "</tr>\n";
                        }
                    });
                    html += "</tbody>\n";
                    html += "</table>\n";
                    title = "Sync Status";
                    attachElem(event, html, title);
                };

                scope.showSourceSummary = function(event) {
                    try{
                        var elem = $(event.target).parent();
                        // if the popover is visible already, then exit the function here
                        if(elem.data()['bs.popover'].tip().hasClass('in')){
                            return;
                        }
                    }
                    catch(err){
                        scope.gatherSourceJobs(event);
                    }
                };
            }
        };
    }
];
