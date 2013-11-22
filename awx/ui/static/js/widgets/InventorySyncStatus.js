/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 * InventorySyncStatus.js 
 *
 * Dashboard widget showing object counts and license availability.
 *
 */

angular.module('InventorySyncStatusWidget', ['RestServices', 'Utilities'])
    .factory('InventorySyncStatus', ['$rootScope', '$compile', 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait', 'GetChoices',
    function($rootScope, $compile, Rest, GetBasePath, ProcessErrors, Wait, GetChoices) {
    return function(params) {
        
        var scope = params.scope;
        var target = params.target;
        var dashboard = params.dashboard;  
  
        var html = "<div class=\"panel panel-default\">\n";
        html += "<div class=\"panel-heading\">Inventory Sync Status</div>\n";
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
            var label = params.label;
            var count = params.count; 
            var fail = params.fail; 
            var link = params.link; 
            var fail_link = params.fail_link;
            var html = "<tr>\n";
            html += "<td><a href=\"" + link + "\"";
            html += (label == 'Hosts' || label == 'Groups') ? " class=\"pad-left-sm\" " : "";
            html += ">"  + label + "</a></td>\n";
            html += "<td class=\"failed-column text-right\">";
            html += "<a href=\"" + fail_link + "\">" + fail + "</a>";
            html += "</td>\n";
            html += "<td class=\"text-right\">";
            html += "<a href=\"" + link + "\">" + count + "</a>";
            html += "</td></tr>\n";
            return html; 
            }

        html += makeRow({ label: 'Inventories',
            count: [(dashboard.inventories && dashboard.inventories.total_with_inventory_source) ? 
                dashboard.inventories.total_with_inventory_source : 0 ], 
            fail: [(dashboard.inventories && dashboard.inventories.inventory_failed) ? dashboard.inventories.inventory_failed : 0], 
            link: '/#/inventories/?has_inventory_sources=true', 
            fail_link: '/#/inventories/?inventory_sources_with_failures=true'
            });
        
        var group_total = 0;
        var group_fail = 0;
        if (dashboard.inventory_sources) {
            for (var src in dashboard.inventory_sources) {
                group_total += (dashboard.inventory_sources[src].total) ? dashboard.inventory_sources[src].total : 0;
                group_fail += (dashboard.inventory_sources[src].failed) ? dashboard.inventory_sources[src].failed : 0;
            }
        }
        
        html += makeRow({ label: 'Groups',
            count: group_total,
            fail: group_fail,
            link: '/#/home/groups/?has_external_source=true',
            fail_link: '/#/home/groups/?status=failed'
            });

        // Each inventory source
        for (var src in dashboard.inventory_sources) {
            if (dashboard.inventory_sources[src].total) {
                html += makeRow({ label: dashboard.inventory_sources[src].label, 
                    count: [(dashboard.inventory_sources[src].total) ? dashboard.inventory_sources[src].total : 0], 
                    fail: [(dashboard.inventory_sources[src].failed) ? dashboard.inventory_sources[src].failed : 0],
                    link: '/#/home/groups/?source=' + src,
                    fail_link: '/#/home/groups/?status=failed&source=' + src
                    });
            }
        }

        html += "</tbody>\n";
        html += "</table>\n";
        html += "</div>\n";
        html += "</div>\n";
        html += "</div>\n";
        
        var element = angular.element(document.getElementById(target));
        element.html(html);
        $compile(element)(scope);
        scope.$emit('WidgetLoaded');

        }
        }]);