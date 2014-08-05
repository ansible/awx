/******************************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  helpers/Access.js
 *
 *  Routines for checking user access
 *
 */

'use strict';

angular.module('AccessHelper', ['RestServices', 'Utilities'])

    .factory('CheckAccess', ['$rootScope', 'Alert', 'Rest', 'GetBasePath', 'ProcessErrors', function ($rootScope, Alert, Rest, GetBasePath, ProcessErrors) {
        return function (params) {
            // set PermissionAddAllowed to true or false based on user access. admins and org admins are granted
            // accesss.
            var me = $rootScope.current_user,
                scope = params.scope;

            if (me.is_superuser) {
                scope.PermissionAddAllowed = true;
            } else {
                if (me.related.admin_of_organizations) {
                    Rest.setUrl(me.related.admin_of_organizations);
                    Rest.get()
                        .success(function (data) {
                            if (data.results.length > 0) {
                                scope.PermissionAddAllowed = true;
                            } else {
                                scope.PermissionAddAllowed = false;
                            }
                        })
                        .error(function (data, status) {
                            ProcessErrors(scope, data, status, null, {
                                hdr: 'Error!',
                                msg: 'Call to ' + me.related.admin_of_organizations +
                                    ' failed. DELETE returned status: ' + status
                            });
                        });
                }
            }
            //if (!access) {
            //   Alert('Access Denied', 'You do not have access to this function. Please contact your system administrator.');
            //}
            //return access;
        };
    }])

    .factory('IsAdmin', ['$rootScope', function($rootScope) {
        return function() { return ($rootScope.current_user && $rootScope.current_user.is_superuser); };
    }]);
