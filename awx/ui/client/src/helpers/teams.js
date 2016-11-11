/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name helpers.function:teams
 * @description
 *  TeamHelper
 *  Routines shared amongst the team controllers
 */

import listGenerator from '../shared/list-generator/main';

export default
    angular.module('TeamHelper', ['RestServices', 'Utilities', 'OrganizationListDefinition', listGenerator.name
    ])
        .factory('SetTeamListeners', ['Alert', 'Rest',
            function (Alert, Rest) {
                return function (params) {

                    var scope = params.scope,
                        set = params.set;

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

                            // @issue: OLD SEARCH
                            // scope[iterator + 'SearchSpin'] = false;

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
    ]);
