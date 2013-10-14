/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
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
        
        var current_version; 
        var scope = $rootScope.$new();
        var counts = {};
        var target = params.target;
        var expected;
        
        if (scope.removeCountReady) {
           scope.removeCountReady();
        }
        scope.removeCountReady = scope.$on('countReady', function(e, obj, count) {
            var keys=[ 'organizations', 'users', 'teams', 'projects', 'inventory', 'groups', 'hosts',
                'credentials', 'job_templates', 'jobs' ];
            var html, itm;
            var cnt = 0;
            for (itm in counts) {
                cnt++;
            }
            if (cnt == expected) {
               // sort the list of objs
               //for (var key in counts) {
               //    if (key !== 'hosts' && key !== 'groups') {
               //      keys.push(key);
               //    }
               //}
               // sort the keys, forcing groups and hosts to appear directlry after inventory
               //keys.sort();
               //var new_keys = [];
               //for (var i=0; i < keys.length; i++) {
               //    if (keys[i] == 'inventory') {
               //       new_keys.push('inventory');
               //       new_keys.push('groups');
               //       new_keys.push('hosts');
               //    } 
               //    else {
               //       new_keys.push(keys[i]);
               //    }
               //}
               //keys = new_keys; 
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
               for (var i=0; i < keys.length; i++) {
                   html += "<tr><td class=\"capitalize\">\n";
                   html += "<a href=\"/#/";
                   html += (keys[i] == 'inventory') ? 'inventories' : keys[i];
                   html += "\"";
                   html += (keys[i] == 'hosts' || keys[i] == 'groups') ? " class=\"pad-left-sm\" " : "";
                   html += ">";
                   if (keys[i] == 'inventory') {
                      html += 'Inventories';
                   }
                   else {
                      html += keys[i].replace(/\_/g,' ');
                      //html += txt.substring(0,1).toUpperCase() + txt.substring(1);
                   }
                   html += "</a></td>\n"
                   html += "<td class=\"text-right\"><a href=\"/#/";
                   html += (keys[i] == 'inventory') ? 'inventories' : keys[i];
                   html += "\">";
                   html += counts[keys[i]] + "</a></td></tr>\n";
               }
               html += "</tbody>\n";
               html += "</table>\n";
               html += "</div>\n";
               html += "</div>\n"
               var element = angular.element(document.getElementById(target));
               element.html(html);
               $compile(element)(scope);
               $rootScope.$emit('WidgetLoaded');
            }
            });

        var getCount = function (obj) {
            scope.collection = (obj == 'inventory') ? 'inventories' : obj;
            var url = current_version + scope.collection + '/'; 
            Rest.setUrl(url);
            Rest.get()
                .success( function(data, status, headers, config) {
                    counts[obj] = data.count;
                    scope.$emit('countReady');
                    })
                .error( function(data, status, headers, config) {
                    ProcessErrors(scope, data, status, null,
                        { hdr: 'Error!', msg: 'Failed to get count for ' + obj + '. GET status: ' + status });
                    });
             }

        Rest.setUrl('/api/');
        Rest.get()
            .success( function(data, status, headers, config) {
                
                current_version = data.current_version;
                
                Rest.setUrl(current_version);
                Rest.get()
                    .success( function(data, status, headers, config) {
                        for (var obj in data) {
                            if (obj == 'me' || obj == 'authtoken' || obj == 'config' || obj == 'inventory_sources') {
                               delete data[obj]; 
                            }
                        }
                        expected = 0;
                        for (var obj in data) {
                            expected++;
                        }
                        for (obj in data) {
                            getCount(obj);
                        }
                        })
                    .error( function(data, status, headers, config) {
                        ProcessErrors(scope, data, status, null,
                            { hdr: 'Error!', msg: 'Failed to get ' + current_version + '. GET status: ' + status });
                        })
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get /api/. GET status: ' + status });
                });
        }
        }]);
