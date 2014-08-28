/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  ProjectPathHelper
 */
    /**
 * @ngdoc function
 * @name helpers.function:ProjectPath
 * @description
 *  Use GetProjectPath({ scope: <scope>, master: <master obj> }) to
 *  load scope.project_local_paths (array of options for drop-down) and
 *  scope.base_dir (readonly field).
 *
 */
angular.module('ProjectPathHelper', ['RestServices', 'Utilities'])
    .factory('GetProjectPath', ['Alert', 'Rest', 'GetBasePath', 'ProcessErrors',
        function (Alert, Rest, GetBasePath, ProcessErrors) {
            return function (params) {

                var scope = params.scope,
                    master = params.master;

                function arraySort(data) {
                    //Sort nodes by name
                    var i, j, names = [],
                        newData = [];
                    for (i = 0; i < data.length; i++) {
                        names.push(data[i].value);
                    }
                    names.sort();
                    for (j = 0; j < names.length; j++) {
                        for (i = 0; i < data.length; i++) {
                            if (data[i].value === names[j]) {
                                newData.push(data[i]);
                            }
                        }
                    }
                    return newData;
                }

                scope.showMissingPlaybooksAlert = false;

                Rest.setUrl(GetBasePath('config'));
                Rest.get()
                    .success(function (data) {
                        var opts = [], i;
                        for (i = 0; i < data.project_local_paths.length; i++) {
                            opts.push({
                                label: data.project_local_paths[i],
                                value: data.project_local_paths[i]
                            });
                        }
                        if (scope.local_path) {
                            // List only includes paths not assigned to projects, so add the
                            // path assigned to the current project.
                            opts.push({
                                label: scope.local_path,
                                value: scope.local_path
                            });
                        }
                        scope.project_local_paths = arraySort(opts);
                        if (scope.local_path) {
                            for (i = 0; scope.project_local_paths.length; i++) {
                                if (scope.project_local_paths[i].value === scope.local_path) {
                                    scope.local_path = scope.project_local_paths[i];
                                    break;
                                }
                            }
                        }
                        scope.base_dir = data.project_base_dir;
                        master.local_path = scope.local_path;
                        master.base_dir = scope.base_dir; // Keep in master object so that it doesn't get
                        // wiped out on form reset.
                        if (opts.length === 0) {
                            // trigger display of alert block when scm_type == manual
                            scope.showMissingPlaybooksAlert = true;
                        }
                    })
                    .error(function (data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to access API config. GET status: ' + status });
                    });
            };
        }
    ]);