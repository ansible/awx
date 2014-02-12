/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * JobStatus.js
 *
 * Dashboard widget showing object counts and license availability.
 *
 */

'use strict';

angular.module('JobStatusWidget', ['RestServices', 'Utilities'])
    .factory('JobStatus', ['$rootScope', '$compile', 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait',
        function ($rootScope, $compile) {
            return function (params) {

                var scope = params.scope,
                    target = params.target,
                    dashboard = params.dashboard,
                    html = '', element;
                
                html = "<div class=\"panel panel-default\">\n";
                html += "<div class=\"panel-heading\">Job Status</div>\n";
                html += "<div class=\"panel-body\">\n";
                html += "<table class=\"table table-condensed table-hover\">\n";
                html += "<thead>\n";
                html += "<tr>\n";
                html += "<th class=\"col-md-4 col-lg-3\"></th>\n";
                html += "<th class=\"col-md-2 col-lg-1 text-right\">Failed</th>\n";
                html += "<th class=\"col-md-2 col-lg-1 text-right\">Total</th>\n";
                html += "</tr>\n";
                html += "</thead>\n";
                html += "<tbody>\n";

                function makeRow(params) {
                    var html = '',
                        label = params.label,
                        link = params.link,
                        fail_link = params.fail_link,
                        count = params.count,
                        fail = params.fail;
                    html += "<tr>\n";
                    html += "<td><a href=\"" + link + "\"";
                    html += (label === 'Hosts' || label === 'Groups') ? " class=\"pad-left-sm\" " : "";
                    html += ">" + label + "</a></td>\n";
                    html += "<td class=\"";
                    html += (fail > 0) ? 'failed-column' : 'zero-column';
                    html += " text-right\">";
                    html += "<a href=\"" + fail_link + "\">" + fail + "</a>";
                    html += "</td>\n";
                    html += "<td class=\"text-right\">";
                    html += "<a href=\"" + link + "\" >" + count + "</a>";
                    html += "</td></tr>\n";
                    return html;
                }

                html += makeRow({
                    label: 'Jobs',
                    link: '/#/jobs',
                    count: (dashboard.jobs && dashboard.jobs.total) ? dashboard.jobs.total : 0,
                    fail: (dashboard.jobs && dashboard.jobs.failed) ? dashboard.jobs.failed : 0,
                    fail_link: '/#/jobs/?status=failed'
                });
                html += makeRow({
                    label: 'Inventories',
                    link: '/#/inventories',
                    count: (dashboard.inventories && dashboard.inventories.total) ? dashboard.inventories.total : 0,
                    fail: (dashboard.inventories && dashboard.inventories.job_failed) ? dashboard.inventories.job_failed : 0,
                    fail_link: '/#/inventories/?has_active_failures=true'
                });
                html += makeRow({
                    label: 'Groups',
                    link: '/#/home/groups',
                    count: (dashboard.groups && dashboard.groups.total) ? dashboard.groups.total : 0,
                    fail: (dashboard.groups && dashboard.groups.job_failed) ? dashboard.groups.job_failed : 0,
                    fail_link: '/#/home/groups/?has_active_failures=true'
                });
                html += makeRow({
                    label: 'Hosts',
                    link: '/#/home/hosts',
                    count: (dashboard.hosts && dashboard.hosts.total) ? dashboard.hosts.total : 0,
                    fail: (dashboard.hosts && dashboard.hosts.failed) ? dashboard.hosts.failed : 0,
                    fail_link: '/#/home/hosts/?has_active_failures=true'
                });

                html += "</tbody>\n";
                html += "</table>\n";
                html += "</div>\n";
                html += "</div>\n";
                html += "</div>\n";

                element = angular.element(document.getElementById(target));
                element.html(html);
                $compile(element)(scope);
                scope.$emit('WidgetLoaded');

            };
        }
    ]);