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
        var inventoryCount, inventoryFails, groupCount, groupFails, hostCount;
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
            
            function makeRow(label, count, fail) {
                var html = "<tr>\n";
                html += "<td><a href=\"/#/" + label.toLowerCase() + "\">"  + label + "</a></td>\n";
                html += "<td class=\"failed-column text-right\">";
                html += (fail > 0) ? "<a href=\"/blah/blah\">" + fail + "</a>" : "";
                html += "</td>\n";
                html += "<td class=\"text-right\">";
                html += (count > 0) ? "<a href=\"/blah/blah\">" + count + "</a>" : "";
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
                  html += makeRow('Inventories', inventoryCount, inventoryFails);
                  rowcount++;
               }
               if (groupCount > 0) {
                  html += makeRow('Groups', groupCount, groupFails);
                  rowcount++;
               }
               if (hostCount > 0) {
                  html += makeRow('Hosts', hostCount, hostFails);
                  rowcount++;
               }

               for (var i=0; i < results.length; i++) {
                   if (results[i].count > 0) {
                      html += makeRow(results[i].label, results[i].count, results[i].fail);
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
        
        inventoryFails = 0;
        
        url = GetBasePath('inventory_sources') + '?source__in=ec2,rackspace&page=1';
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

        url = GetBasePath('inventory_sources') + '?status=failed&source__in=ec2,rackspace&page=1';
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
        
        url = GetBasePath('hosts') + '?has_inventory_sources=true&page=1';
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

        scope.removeTypesReady = scope.$on('TypesReady', function (e, label, count, fail) {
            results.push({ label: label, count: count, fail: fail });  
            if (results.length == expected) {
               scope.$emit('CountReceived');
            }
            });

        scope.removeCountProjects = scope.$on('CountTypes', function(e, choices) {
            
            scm_choices = choices; 

            function getLabel(config) {
                var url = config.url; 
                var type = url.match(/source=.*\&/)[0].replace(/source=/,'').replace(/\&/,'');
                var label;
                for (var i=0; i < choices.length; i++) {
                   if (choices[i][0] == type) {
                      label = choices[i][1];
                      break;
                   }
                }
                return label;   
                }
            
            // Remove ---- option from list of choices
            for (var i=0; i < choices.length; i++) {
                if (choices[i][1].match(/^---/)) {
                   choices.splice(i,1);
                   break;
                }
            }

            for (var i=0; i < choices.length; i++) {
                if (choices[i][1].match(/^Local/)) {
                   choices.splice(i,1);
                   break;
                }
            }
            
            expected = choices.length; 

            for (var i=0; i < choices.length; i++) {
                if (!choices[i][1].match(/^---/)) {
                   var url = GetBasePath('inventory_sources') + '?source=' + choices[i][0] + '&page=1';
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
                           scope.$emit('TypesReady', label, count, fail);
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
            field: 'source',
            emit: 'CountTypes' });

        }
        }]);