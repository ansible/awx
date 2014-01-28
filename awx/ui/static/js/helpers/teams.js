/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  TeamHelper
 *  Routines shared amongst the team controllers 
 */
 
angular.module('TeamHelper', [ 'RestServices', 'Utilities', 'OrganizationListDefinition',
                               'SearchHelper', 'PaginationHelpers', 'ListGenerator' ])  
    .factory('SetTeamListeners', ['Alert', 'Rest', function(Alert, Rest) {
    return function(params) {
 
        var scope = params.scope; 
        var set = params.set; 
        var iterator = params.iterator; 

        // Listeners to perform lookups after main inventory list loads

        scope.$on('TeamResultFound', function(e, results, lookup_results) {
            if ( lookup_results.length == results.length ) {
               key = 'organization';
               property = 'organization_name';
               for (var i=0; i < results.length; i++) {
                   for (var j=0; j < lookup_results.length; j++) {
                       if (results[i][key] == lookup_results[j].id) {
                          results[i][property] = lookup_results[j].value;
                       }
                   }
               }
               scope[iterator + 'SearchSpin'] = false;
               scope[set] = results;
            }
            });

        scope.$on('TeamRefreshFinished', function(e, results) {
            // Loop through the result set (sent to us by the search helper) and
            // lookup the id and name of each organization. After each lookup 
            // completes, call resultFound.
            
            var lookup_results = [];
            
            for (var i = 0; i < results.length; i++) {
                Rest.setUrl('/api/v1/organizations/' + results[i].organization + '/');
                Rest.get()
                   .success( function( data, status, headers, config) {
                      lookup_results.push({ id: data.id, value: data.name });
                      scope.$emit('TeamResultFound', results, lookup_results);
                      })
                   .error( function( data, status, headers, config) {
                      lookup_results.push({ id: 'error' });
                      scope.$emit('TeamResultFound', results, lookup_results);
                      });
            }
            });
        }
        }])
    
    .factory('TeamLookUpOrganizationInit', ['Alert', 'Rest', 'OrganizationList', 'GenerateList', 'SearchInit', 'PaginateInit', 
    function(Alert, Rest, OrganizationList, GenerateList, SearchInit, PaginateInit) {
    return function(params) {
        
        var scope = params.scope;

        // Show pop-up to select organization
        scope.lookUpOrganization = function() {
            var list = OrganizationList; 
            var listGenerator = GenerateList;
            var listScope = listGenerator.inject(list, { mode: 'lookup', hdr: 'Select Organization' });
            var defaultUrl = '/api/v1/organizations/';

            listScope.selectAction = function() {
                var found = false;
                for (var i=0; i < listScope[list.name].length; i++) {
                    if (listScope[list.iterator + "_" + listScope[list.name][i].id + "_class"] == "success") {
                       found = true; 
                       scope['organization'] = listScope[list.name][i].id;
                       scope['organization_name'] = listScope[list.name][i].name;
                       scope['team_form'].$setDirty();
                       listGenerator.hide();
                    }
                } 
                if (found == false) {
                   Alert('No Selection', 'Click on a row to select an Organization before clicking the Select button.');
                }
                }

            listScope.toggle_organization = function(id) {
                // when user clicks a row, remove 'success' class from all rows except clicked-on row
                if (listScope[list.name]) {
                   for (var i=0; i < listScope[list.name].length; i++) {
                       listScope[list.iterator + "_" + listScope[list.name][i].id + "_class"] = ""; 
                   }
                }
                if (id != null && id != undefined) {
                   listScope[list.iterator + "_" + id + "_class"] = "success";
                }
                }

            SearchInit({ scope: listScope, set: list.name, list: list, url: defaultUrl });
            PaginateInit({ scope: listScope, list: list, url: defaultUrl, mode: 'lookup' });
            scope.search(list.iterator);
            listScope.toggle_organization(scope.organization);
            }
        }
        }]);


