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
        
        var scope = $rootScope.$new();
        var target = params.target;
        var expected = 0;
        var results = [];
        var scm_choices;
        
        if (scope.removeCountReceived) {
           scope.removeCountReceived();
        }
        scope.removeCountReceived = scope.$on('CountReceived', function(e, label, count, fail) {
            
            var rowcount = 0;

            function makeRow(label, count, fail) {
                var value; 
                for (var i=0; i < scope['projectChoices'].length; i++) {
                    if (scope['projectChoices'][i].label == label) {
                       value = scope['projectChoices'][i].value;
                       break;
                    }
                }
                var html = ''
                html += "<tr><td><a href=\"/#/projects/?source_type=" + value + "\">"  + label + "</a></td>\n";
                html += "<td class=\"failed-column text-right\">";
                html += "<a href=\"/blah/blah\">" + fail + "</a>";
                html += "</td>\n"; 
                html += "<td class=\"text-right\">";
                html += "<a href=\"/blah/blah\">" + count + "</a>";
                html += "</td>\n";
                html += "</tr>\n";
                return html; 
                }
            
            results.push({ label: label, count: count, fail: fail });
            
            if (results.length == expected) {
               // all the counts came back, now generate the HTML 
               
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

               for (var i=0; i < results.length; i++) {
                   if (results[i].count > 0) {
                      html += makeRow(results[i].label, results[i].count, results[i].fail);
                      rowcount++;
                   }
               }
               if (rowcount == 0) {
                  html += "<tr><td colspan=\"3\">No projects configured for SCM sync</td></tr>\n";
               }

               html += "</tbody>\n";
               html += "</table>\n";
               html += "</div>\n";
               html += "</div>\n";
               html += "</div>\n";

               var element = angular.element(document.getElementById(target));
               element.html(html);
               $compile(element)(scope);
               $rootScope.$emit('WidgetLoaded');
            }
            });
      

        scope.removeCountProjects = scope.$on('CountProjects', function() {
            
            var choices = scope['projectChoices']; 

            function getScmLabel(config) {
                var url = config.url; 
                var scm_type = url.match(/scm_type=.*\&/)[0].replace(/scm_type=/,'').replace(/\&/,'');
                var label;
                for (var i=0; i < choices.length; i++) {
                   if (choices[i].value == scm_type) {
                      label = choices[i].label;
                      break;
                   }
                }
                return label;   
                }
            
            // Remove ---- option from list of choices
            for (var i=0; i < choices.length; i++) {
                if (choices[i].value.match(/^---/)) {
                   choices.splice(i,1);
                   break;
                }
            }
            // Remove Manual option from list of choices
            for (var i=0; i < choices.length; i++) {
                if (choices[i].label.match(/Manual/)) {
                   choices.splice(i,1);
                   break;
                }
            }
            
            expected = choices.length; 

            for (var i=0; i < choices.length; i++) {
                if (!choices[i].label.match(/^---/)) {
                   var url = GetBasePath('projects') + '?scm_type=' + choices[i].value + '&page=1';
                   Rest.setUrl(url);
                   Rest.get()
                       .success( function(data, status, headers, config) {
                           // figure out the scm_type we're looking at and its label
                           var label = getScmLabel(config);
                           var count = data.count; 
                           var fail = 0;
                           for (var i=0; i < data.results.length; i++) {
                               if (data.results[i].status == 'failed') {
                                  fail++;
                               }
                           }
                           scope.$emit('CountReceived', label, count, fail);
                           })
                       .error( function(data, status, headers, config) {
                           ProcessErrors(scope, data, status, null,
                               { hdr: 'Error!', msg: 'Failed to get ' + url + '. GET status: ' + status });
                           });
                }
            }
            });

        GetChoices({
            scope: scope,
            url: GetBasePath('projects'),
            variable: 'projectChoices',
            field: 'scm_type',
            callback: 'CountProjects'
            });

        }
        }]);