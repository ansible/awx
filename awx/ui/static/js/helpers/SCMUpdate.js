/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  SCMUpdate.js
 *
 *  Use to kick off an update the project 
 *
 */

angular.module('SCMUpdateHelper', ['RestServices', 'Utilities'])  
    .factory('SCMUpdate', ['Alert', 'Rest', 'GetBasePath','ProcessErrors',
    function(Alert, Rest, GetBasePath, ProcessErrors) {
    return function(params) {
        
        var scope = params.scope;
        var project = params.project; 

        Rest.setUrl(project.related.update);
        Rest.get()
            .success( function(data, status, headers, config) {
                console.log(data);
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                   { hdr: 'Error!', msg: 'Failed to access ' + project.related.update + '. GET status: ' + status });
                });
        }
        }]);