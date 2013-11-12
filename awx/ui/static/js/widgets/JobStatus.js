/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 * JobStatus.js 
 *
 * Dashboard widget showing object counts and license availability.
 *
 */

angular.module('JobStatusWidget', ['RestServices', 'Utilities'])
    .factory('JobStatus', ['$rootScope', '$compile', 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait',
    function($rootScope, $compile, Rest, GetBasePath, ProcessErrors, Wait) {
    return function(params) {
        
        var scope = $rootScope.$new();
        var jobCount = 0;
        var jobFails = 0; 
        var inventoryCount = 0;
        var inventoryFails = 0;
        var groupCount = 0;
        var groupFails = 0;
        var hostCount = 0;
        var hostFails = 0; 
        var counts = 0;
        var expectedCounts = 8;
        var target = params.target;        

        if (scope.removeCountReceived) {
           scope.removeCountReceived();
        }
        scope.removeCountReceived = scope.$on('CountReceived', function() {

            var rowcount = 0;

            function makeRow(params) {
                var html = '';
                var label = params.label;
                var link = params.link; 
                var fail_link = params.fail_link;
                var count = params.count; 
                var fail = params.fail;
                html += "<tr>\n";
                html += "<td><a href=\"" + link + "\"";
                html += (label == 'Hosts' || label == 'Groups') ? " class=\"pad-left-sm\" " : "";
                html += ">"  + label + "</a></td>\n";
                html += "<td class=\"failed-column text-right\">";
                html += "<a href=\"" + fail_link + "\">" + fail + "</a>"; 
                html += "</td>\n";
                html += "<td class=\"text-right\">"
                html += "<a href=\"" + link + "\" >" + count + "</a>";
                html += "</td></tr>\n";
                return html; 
                }

            counts++;
            if (counts == expectedCounts) {
               // all the counts came back, now generate the HTML 
               var html = "<div class=\"panel panel-default\">\n";
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

               if (jobCount > 0) {
                   html += makeRow({
                       label: 'Jobs',
                       link: '/#/jobs',
                       count: jobCount,
                       fail: jobFails,
                       fail_link: '/#/jobs/?status=failed'
                       });
                  rowcount++;
               }
               if (inventoryCount > 0) {
                   html += makeRow({
                       label: 'Inventories', 
                       link: '/#/inventories',
                       count: inventoryCount,
                       fail: inventoryFails,
                       fail_link: '/#/inventories/?has_active_failures=true' 
                       });
                   rowcount++;
               }
               if (groupCount > 0) {
                   html += makeRow({
                       label: 'Groups', 
                       link: '/#/home/groups',
                       count: groupCount,
                       fail: groupFails,
                       fail_link: '/#/home/groups/?has_active_failures=true' 
                       });
                  rowcount++;
               }
               if (hostCount > 0) {
                   html += makeRow({
                       label: 'Hosts',
                       link: '/#/home/hosts',
                       count: hostCount,
                       fail: hostFails,
                       fail_link: '/#/home/hosts/?has_active_failures=true'
                       });
                  rowcount++;
               }
              
               if (rowcount == 0) {
                  html += "<tr><td colspan=\"3\">No job data found</td></tr>\n";
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

        var url = GetBasePath('jobs') + '?page=1';
        Rest.setUrl(url);
        Rest.get()
            .success( function(data, status, headers, config) {
                jobCount=data.count;
                scope.$emit('CountReceived');
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get ' + url + '. GET status: ' + status });
                });

        url = GetBasePath('jobs') + '?failed=true&page=1';
        Rest.setUrl(url);
        Rest.get()
            .success( function(data, status, headers, config) {
                jobFails=data.count;
                scope.$emit('CountReceived');
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get ' + url + '. GET status: ' + status });
                });

        url = GetBasePath('inventory') + '?page=1';
        Rest.setUrl(url);
        Rest.get()
            .success( function(data, status, headers, config) {
                inventoryCount=data.count;
                scope.$emit('CountReceived');
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get ' + url + '. GET status: ' + status });
                });

        url = GetBasePath('inventory') + '?has_active_failures=true&page=1';
        Rest.setUrl(url);
        Rest.get()
            .success( function(data, status, headers, config) {
                inventoryFails=data.count;
                scope.$emit('CountReceived');
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get ' + url + '. GET status: ' + status });
                });

        url = GetBasePath('groups') + '?page=1';
        Rest.setUrl(url);
        Rest.get()
            .success( function(data, status, headers, config) {
                groupCount = data.count;
                scope.$emit('CountReceived');
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get ' + url + '. GET status: ' + status });
                });

        url = GetBasePath('groups') + '?has_active_failures=true&page=1';
        Rest.setUrl(url);
        Rest.get()
            .success( function(data, status, headers, config) {
                groupFails = data.count;
                scope.$emit('CountReceived');
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get ' + url + '. GET status: ' + status });
                });

        url = GetBasePath('hosts') + '?page=1';
        Rest.setUrl(url);
        Rest.get()
            .success( function(data, status, headers, config) {
                hostCount = data.count;
                scope.$emit('CountReceived');
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get ' + url + '. GET status: ' + status });
                });

        url = GetBasePath('hosts') + '?has_active_failures=true&page=1';
        Rest.setUrl(url);
        Rest.get()
            .success( function(data, status, headers, config) {
                hostFails = data.count;
                scope.$emit('CountReceived');
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get ' + url + '. GET status: ' + status });
                });

        }
        }]);
