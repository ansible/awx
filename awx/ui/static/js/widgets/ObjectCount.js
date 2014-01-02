/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * ObjectCount.js 
 *
 * Dashboard widget showing object counts and license availability.
 *
 */


angular.module('ObjectCountWidget', ['RestServices', 'Utilities'])
    .factory('ObjectCount', ['$rootScope', '$compile', 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait',
    function($rootScope, $compile, Rest, GetBasePath, ProcessErrors, Wait) {
    return function(params) {
        
        var scope = params.scope;
        var target = params.target;
        var dashboard = params.dashboard; 
        
        
        var keys=[ 'organizations', 'users', 'teams', 'credentials', 'projects', 'inventories', 'groups', 'hosts',
            'job_templates', 'jobs' ];
            
        html = "<div class=\"panel panel-default\">\n";
        html += "<div class=\"panel-heading\">System Summary</div>\n";
        html += "<div class=\"panel-body\">\n";
        html += "<table class=\"table table-condensed table-hover\">\n";
        html += "<thead>\n";
        html += "<tr>\n";
        html += "<th class=\"col-md-5 col-lg-4\"></th>\n";
        html += "<th class=\"col-md-1 col-lg-1 text-right\">Total</th>\n";
        html += "</tr>\n";
        html += "</thead>\n";
        html += "<tbody>\n";
       
        function makeRow(params) {
            var html = '';
            var label = params.label;
            var link = params.link; 
            var count = params.count; 
            html += "<tr>\n";
            html += "<td class=\"capitalize\"><a href=\"" + link + "\"";
            html += (label == 'hosts' || label == 'groups') ? " class=\"pad-left-sm\" " : "";
            html += ">"  + label.replace(/\_/g,' ') + "</a></td>\n";
            html += "<td class=\"text-right\">"
            html += "<a href=\"" + link + "\" >" + count + "</a>";
            html += "</td></tr>\n";
            return html; 
            }      
        
        for (var i=0; i < keys.length; i++) {
            html += makeRow({
                label: keys[i],
                link: '/#/' + [(keys[i] == 'hosts' || keys[i] == 'groups') ? 'home/' + keys[i] : keys[i] ],
                count: [(dashboard[keys[i]] && dashboard[keys[i]].total) ? dashboard[keys[i]].total : 0]
                });
        }

        html += "</tbody>\n";
        html += "</table>\n";
        html += "</div>\n";
        html += "</div>\n"
        var element = angular.element(document.getElementById(target));
        element.html(html);
        $compile(element)(scope);
        scope.$emit('WidgetLoaded');
        
        }
        }]);