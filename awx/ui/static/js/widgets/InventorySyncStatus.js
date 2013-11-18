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
        
        var scope = $rootScope.$new();
        var inventoryCount = 0;
        var inventoryFails = 0;
        var groupCount = 0;
        var groupFails = 0;
        var hostCount = 0;
        var hostFails = 0; 
        var counts = 0;
        var expectedCounts = 5;
        var target = params.target;
        var results = [];
        var expected;      
        
        if (scope.removeCountReceived) {
           scope.removeCountReceived();
        }
        scope.removeCountReceived = scope.$on('CountReceived', function() {

            var rowcount = 0;
            
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

            counts++;
            if (counts == expectedCounts) {
               // all the counts came back, now generate the HTML 
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
               
               if (inventoryCount > 0) {
                   html += makeRow({ label: 'Inventories',
                       count: inventoryCount, 
                       fail: inventoryFails, 
                       link: '/#/inventories/?has_inventory_sources=true', 
                       fail_link: '/#/inventories/?inventory_sources_with_failures=true' });
                   rowcount++;
               }
               if (groupCount > 0) {
                   html += makeRow({ label: 'Groups',
                       count: groupCount,
                       fail: groupFails,
                       link: '/#/home/groups/?has_external_source=true',
                       fail_link: '/#/home/groups/?status=failed' });
                  rowcount++;
               }
               for (var i=0; i < results.length; i++) {
                   if (results[i].count > 0) {
                      html += makeRow({ label: results[i].label, 
                          count: results[i].count, 
                          fail: results[i].fail,
                          link: '/#/home/groups/?source=' + results[i].source,
                          fail_link: '/#/home/groups/?status=failed&source=' + results[i].source });
                      rowcount++;
                   }
               }

               if (rowcount == 0) {
                  html += "<tr><td colspan=\"3\">No inventories configured for external sync</td></tr>\n";
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

        var url = GetBasePath('inventory') + '?has_inventory_sources=true&page=1';
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
        
        var url = GetBasePath('inventory') + '?inventory_sources_with_failures__gt=0&page=1';
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
        
        url = GetBasePath('inventory_sources') + '?source__in=ec2,rax&page=1';
        Rest.setUrl(url);
        Rest.get()
            .success( function(data, status, headers, config) {
                groupCount=data.count;
                scope.$emit('CountReceived');
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get ' + url + '. GET status: ' + status });
                });

        url = GetBasePath('inventory_sources') + '?status=failed&source__in=ec2,rax&page=1';
        Rest.setUrl(url);
        Rest.get()
            .success( function(data, status, headers, config) {
                groupFails=data.count;
                scope.$emit('CountReceived');
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get ' + url + '. GET status: ' + status });
                });
        
       /* url = GetBasePath('hosts') + '?has_inventory_sources=true&page=1';
        Rest.setUrl(url);
        Rest.get()
            .success( function(data, status, headers, config) {
                hostCount=data.count;
                scope.$emit('CountReceived');
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get ' + url + '. GET status: ' + status });
                });
        */

        if (scope.removeTypesReady) {
            scope.removeTypesReady();
        }
        scope.removeTypesReady = scope.$on('TypesReady', function (e, label, count, fail, source) {
            results.push({ label: label, count: count, fail: fail, source: source });  
            if (results.length == expected) {
               scope.$emit('CountReceived');
            }
            });
        
        if (scope.CountProjects) {
            scope.CountProjects();
        }
        scope.removeCountProjects = scope.$on('CountTypes', function() {
            
            var choices = scope['inventorySources']; 

            function getLabel(config) {
                var url = config.url; 
                var type = url.match(/source=.*\&/)[0].replace(/source=/,'').replace(/\&/,'');
                var label;
                for (var i=0; i < choices.length; i++) {
                   if (choices[i].value == type) {
                      label = choices[i].label;
                      break;
                   }
                }
                return label;   
                }
            
            // Remove ---- option from list of choices
            for (var i=0; i < choices.length; i++) {
                if (choices[i].label.match(/^---/)) {
                   choices.splice(i,1);
                   break;
                }
            }

            for (var i=0; i < choices.length; i++) {
                if (choices[i].label.match(/^Local/)) {
                   choices.splice(i,1);
                   break;
                }
            }
            
            expected = choices.length; 
            
            for (var i=0; i < choices.length; i++) {
                if (!choices[i].label.match(/^---/)) {
                   var url = GetBasePath('inventory_sources') + '?source=' + choices[i].value + '&page=1';
                   Rest.setUrl(url);
                   Rest.get()
                       .success( function(data, status, headers, config) {
                           // figure out the scm_type we're looking at and its label
                           var label = getLabel(config);
                           var count = data.count;
                           var fail = 0;
                           for (var i=0; i < data.results.length; i++) {
                               if (data.results[i].status == 'failed') {
                                  fail++;
                               }
                           }
                           scope.$emit('TypesReady', label, count, fail, 
                                config.url.match(/source=.*\&/)[0].replace(/source=/,'').replace(/\&/,''));
                           })
                       .error( function(data, status, headers, config) {
                           ProcessErrors(scope, data, status, null,
                               { hdr: 'Error!', msg: 'Failed to get ' + url + '. GET status: ' + status });
                           });
                }
            }
            });

        GetChoices({ scope: scope,
            url: GetBasePath('inventory_sources'),
            variable: 'inventorySources',
            field: 'source',
            callback: 'CountTypes' });

        }
        }]);