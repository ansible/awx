/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  ProjectsHelper
 *
 *  Use GetProjectPath({ scope: <scope>, master: <master obj> }) to
 *  load scope.project_local_paths (array of options for drop-down) and
 *  scope.base_dir (readonly field).
 *
 */

'use strict';

angular.module('ProjectsHelper', ['RestServices', 'Utilities', 'ProjectStatusDefinition', 'ProjectFormDefinition'])

    .factory('GetProjectIcon', [ function() {
        return function(status) {
            var result = '';
            switch (status) {
                case 'n/a':
                case 'ok':
                case 'never updated':
                    result = 'none';
                    break;
                case 'pending':
                case 'waiting':
                case 'new':
                    result = 'none';
                    break;
                case 'updating':
                case 'running':
                    result = 'running';
                    break;
                case 'successful':
                    result = 'success';
                    break;
                case 'failed':
                case 'missing':
                    result = 'error';
            }
            return result;
        };
    }])

    .factory('GetProjectToolTip', [ function() {
        return function(status) {
            var result = '';
            switch (status) {
                case 'n/a':
                case 'ok':
                case 'never updated':
                    result = 'No SCM updates have run for this project';
                    break;
                case 'pending':
                case 'waiting':
                case 'new':
                    result = 'Queued. Click for details';
                    break;
                case 'updating':
                case 'running':
                    result = 'Running! Click for details';
                    break;
                case 'successful':
                    result = 'Success! Click for details';
                    break;
                case 'failed':
                case 'missing':
                    result = 'Failed. Click for details';
            }
            return result;
        };
    }]);