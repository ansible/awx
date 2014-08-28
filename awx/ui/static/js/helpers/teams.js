/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 */
/**
 * @ngdoc function
 * @name helpers.function:teams
 * @description
 *  TeamHelper
 *  Routines shared amongst the team controllers
 */

'use strict';

angular.module('TeamHelper', ['RestServices', 'Utilities', 'OrganizationListDefinition', 'SearchHelper',
    'PaginationHelpers', 'ListGenerator'
])
    .factory('SetTeamListeners', ['Alert', 'Rest',
        function (Alert, Rest) {
            return function (params) {

                var scope = params.scope,
                    set = params.set,
                    iterator = params.iterator;

                // Listeners to perform lookups after main inventory list loads

                scope.$on('TeamResultFound', function (e, results, lookup_results) {
                    var i, j, key, property;
                    if (lookup_results.length === results.length) {
                        key = 'organization';
                        property = 'organization_name';
                        for (i = 0; i < results.length; i++) {
                            for (j = 0; j < lookup_results.length; j++) {
                                if (results[i][key] === lookup_results[j].id) {
                                    results[i][property] = lookup_results[j].value;
                                }
                            }
                        }
                        scope[iterator + 'SearchSpin'] = false;
                        scope[set] = results;
                    }
                });

                scope.$on('TeamRefreshFinished', function (e, results) {
                    // Loop through the result set (sent to us by the search helper) and
                    // lookup the id and name of each organization. After each lookup
                    // completes, call resultFound.

                    var i, lookup_results = [], url;

                    function getOrganization(url) {
                        Rest.setUrl(url);
                        Rest.get()
                            .success(function (data) {
                                lookup_results.push({ id: data.id, value: data.name });
                                scope.$emit('TeamResultFound', results, lookup_results);
                            })
                            .error(function () {
                                lookup_results.push({ id: 'error' });
                                scope.$emit('TeamResultFound', results, lookup_results);
                            });
                    }

                    for (i = 0; i < results.length; i++) {
                        url = '/api/v1/organizations/' + results[i].organization + '/';
                        getOrganization(url);
                    }
                });
            };
        }
    ])

.factory('TeamLookUpOrganizationInit', ['Alert', 'Rest', 'OrganizationList', 'GenerateList', 'SearchInit', 'PaginateInit',
    function (Alert, Rest, OrganizationList, GenerateList, SearchInit, PaginateInit) {
        return function (params) {

            var scope = params.scope;

            // Show pop-up to select organization
            scope.lookUpOrganization = function () {
                var list = OrganizationList,
                    listGenerator = GenerateList,
                    listScope = listGenerator.inject(list, { mode: 'lookup', hdr: 'Select Organization' }),
                    defaultUrl = '/api/v1/organizations/';

                listScope.selectAction = function () {
                    var i, found = false;
                    for (i = 0; i < listScope[list.name].length; i++) {
                        if (listScope[list.iterator + "_" + listScope[list.name][i].id + "_class"] === "success") {
                            found = true;
                            scope.organization = listScope[list.name][i].id;
                            scope.organization_name = listScope[list.name][i].name;
                            scope.team_form.$setDirty();
                            listGenerator.hide();
                        }
                    }
                    if (found === false) {
                        Alert('No Selection', 'Click on a row to select an Organization before clicking the Select button.');
                    }
                };

                listScope.toggle_organization = function (id) {
                    // when user clicks a row, remove 'success' class from all rows except clicked-on row
                    if (listScope[list.name]) {
                        for (var i = 0; i < listScope[list.name].length; i++) {
                            listScope[list.iterator + "_" + listScope[list.name][i].id + "_class"] = "";
                        }
                    }
                    if (id !== null && id !== undefined) {
                        listScope[list.iterator + "_" + id + "_class"] = "success";
                    }
                };

                SearchInit({
                    scope: listScope,
                    set: list.name,
                    list: list,
                    url: defaultUrl
                });
                PaginateInit({
                    scope: listScope,
                    list: list,
                    url: defaultUrl,
                    mode: 'lookup'
                });
                scope.search(list.iterator);
                listScope.toggle_organization(scope.organization);
            };
        };
    }
]);