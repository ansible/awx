/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  ProjectPathHelper
 *
 *  Use GetProjectPath({ scope: <scope>, master: <master obj> }) to 
 *  load scope.project_local_paths (array of options for drop-down) and
 *  scope.base_dir (readonly field). 
 *
 */

angular.module('ProjectPathHelper', ['RestServices', 'Utilities'])  
    .factory('GetProjectPath', ['Alert', 'Rest', 'GetBasePath','ProcessErrors',
    function(Alert, Rest, GetBasePath, ProcessErrors) {
    return function(params) {
        
        var scope = params.scope;
        var master = params.master; 

        Rest.setUrl( GetBasePath('config') );
        Rest.get()
            .success( function(data, status, headers, config) {
                var opts = [];
                for (var i=0; i < data.project_local_paths.length; i++) {
                   opts.push(data.project_local_paths[i]);
                } 
                if (scope.local_path) {
                   opts.push(scope.local_path);
                }
                scope.project_local_paths = opts;
                scope.base_dir = data.project_base_dir;
                master.base_dir = scope.base_dir;  // Keep in master object so that it doesn't get
                                                   // wiped out on form reset.
                if (opts.length == 0) {
                   Alert('Missing project path', 'All of the project paths have been assigned to existing projects, or ' +
                       'there are no directories found in the base path. You will need to add a project path before creating ' +
                       'a new project.', 'alert-info');
                }
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                   { hdr: 'Error!', msg: 'Failed to access API config. GET status: ' + status });
                });
        }
        }]);