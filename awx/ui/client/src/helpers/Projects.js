/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

   /**
 * @ngdoc function
 * @name helpers.function:Projects
 * @description
 *  Use GetProjectPath({ scope: <scope>, master: <master obj> }) to
 *  load scope.project_local_paths (array of options for drop-down) and
 *  scope.base_dir (readonly field).
 *
 */


export default
    angular.module('ProjectsHelper', ['RestServices', 'Utilities'])

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
                    case 'canceled':
                        result = 'error';
                }
                return result;
            };
        }])

        .factory('GetProjectToolTip', ['i18n', function(i18n) {
            return function(status) {
                var result = '';
                switch (status) {
                    case 'n/a':
                    case 'ok':
                    case 'never updated':
                        result = i18n._('No SCM updates have run for this project');
                        break;
                    case 'pending':
                    case 'waiting':
                    case 'new':
                        result = i18n._('Queued. Click for details');
                        break;
                    case 'updating':
                    case 'running':
                        result = i18n._('Running! Click for details');
                        break;
                    case 'successful':
                        result = i18n._('Success! Click for details');
                        break;
                    case 'failed':
                        result = i18n._('Failed. Click for details');
                        break;
                    case 'missing':
                        result = i18n._('Missing. Click for details');
                        break;
                    case 'canceled':
                        result = i18n._('Canceled. Click for details');
                        break;
                }
                return result;
            };
        }]);
