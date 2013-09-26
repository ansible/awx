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
        var counts = [];
        var target = params.target;

        scope.$on('countReady', function(e, obj, count) {
            var keys=[];
            var hash = {};
            if (counts.length == 10) {
               // sort the list of objs
               for (var i=0; i < counts.length; i++) {
                   for (var key in counts[i]) {
                       if (key !== 'hosts' && key !== 'groups') {
                          keys.push(key);
                       }
                       hash[key] = counts[i][key];
                   }
               }
               // sort the keys, forcing groups and hosts to appear directlry after inventory
               keys.sort();
               var new_keys = [];
               for (var i=0; i < keys.length; i++) {
                   if (keys[i] == 'inventory') {
                      new_keys.push('inventory');
                      new_keys.push('groups');
                      new_keys.push('hosts');
                   } 
                   else {
                      new_keys.push(keys[i]);
                   }
               }
               keys = new_keys; 

               var html = "<div class=\"panel panel-primary\">\n";
               html += "<div class=\"panel-heading\">System Summary</div>\n";
               html += "<div class=\"panel-body\">\n";
               html += "<ul class=\"list-group grey-txt\">\n";
               for (var i=0; i < keys.length; i++) {
                   html += "<li class=\"list-group-item";
                   html += (keys[i] == 'hosts' || keys[i] == 'groups') ? ' pad-left-md' : ''; 
                   html += "\">\n";
                   html += "<span class=\"badge success-badge\">" + hash[keys[i]] + "</span>\n";
                   
                   if (keys[i] !== 'hosts' && keys[i] !== 'groups') {
                      html += "<a href=\"/#/";
                      html += (keys[i] == 'inventory') ? 'inventories' : keys[i];
                      html += "\">";
                   }
                   
                   if (keys[i] == 'inventory') {
                      html += 'Inventories';
                   }
                   else if (keys[i] == 'job_templates') {
                      html += 'Job Templates';
                   }
                   else {
                      html += keys[i].substring(0,1).toUpperCase() + keys[i].substring(1);
                   }
                   html += (keys[i] !== 'hosts' && keys[i] !== 'groups') ? "</a>" : "";
                   html += "</li>\n";
               }
               html += "</ul>\n";
               html += "</div>\n";
               html += "</div>\n";
               
               var element = angular.element(document.getElementById(target));
               element.html(html);
               //scope = element.scope();   // Set scope specific to the element we're compiling, avoids circular reference
                                          // From here use 'scope' to manipulate the form, as the form is not in '$scope'
               $compile(element)(scope);
            }
            });

        var getCount = function (obj) {
            scope.collection = (obj == 'inventory') ? 'inventories' : obj;
            var url = current_version + scope.collection + '/'; 
            Rest.setUrl(url);
            Rest.get()
                .success( function(data, status, headers, config) {
                    var count = {};
                    count[obj] = data.count;
                    counts.push(count);
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
                        for (obj in data) {
                            if (obj !== 'me' && obj !== 'authtoken' && obj !== 'config') {
                               getCount(obj);
                            }
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
