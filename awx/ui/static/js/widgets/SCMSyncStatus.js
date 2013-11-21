/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 * SCMSyncStatus.js 
 *
 * Dashboard widget showing object counts and license availability.
 *
 */

angular.module('SCMSyncStatusWidget', ['RestServices', 'Utilities'])
    .factory('SCMSyncStatus', ['$rootScope', '$compile', 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait', 'GetChoices',
    function($rootScope, $compile, Rest, GetBasePath, ProcessErrors, Wait, GetChoices) {
    return function(params) {
        
        var scope = params.scope;
        var target = params.target;
        var dashboard = params.dashboard;  
  
        var html = "<div class=\"panel panel-default\">\n";
        html += "<div class=\"panel-heading\">Project SCM Status</div>\n";
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
            var html = '';
            var label = params.label;
            var link = params.link; 
            var fail_link = params.fail_link;
            var count = params.count; 
            var fail = params.fail;
            html += "<tr>\n";
            html += "<td><a href=\"" + link + "\">"  + label + "</a></td>\n";
            html += "<td class=\"failed-column text-right\">";
            html += "<a href=\"" + fail_link + "\">" + fail + "</a>"; 
            html += "</td>\n";
            html += "<td class=\"text-right\">"
            html += "<a href=\"" + link + "\" >" + count + "</a>";
            html += "</td></tr>\n";
            return html; 
            }   

        html += makeRow({ label: 'Projects',
            link: '/#/projects',
            count: [(dashboard.projects && dashboard.projects.total) ? dashboard.projects.total : 0],
            fail: [(dashboard.projects && dashboard.projects.failed) ? dashboard.projects.failed : 0],
            fail_link: '/#/projects/?status=failed'
            });
        
        var labelList = [];
        for (var type in dashboard.scm_types) {
            labelList.push(type);
        }
        labelList.sort();
        var type;
        for (var i=0; i < labelList.length; i++) {
            type = labelList[i];
            if (dashboard.scm_types[type].total) {
                html += makeRow({
                    label: dashboard.scm_types[type].label,
                    link: '/#/projects/?scm_type=' + type,
                    count: [(dashboard.scm_types[type].total) ? dashboard.scm_types[type].total : 0],
                    fail: [(dashboard.scm_types[type].failed) ? dashboard.scm_types[type].failed : 0],
                    fail_link: '/#/projects/?scm_type=' + type + '&status=failed'
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