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

    .factory('CheckAccess', ['$rootScope', 'Alert', 'Rest', 'GetBasePath', 'ProcessErrors', '$cookieStore', function ($rootScope, Alert, Rest, GetBasePath, ProcessErrors, $cookieStore) {
        return function (params) {
            // set PermissionAddAllowed to true or false based on user access. admins and org admins are granted
            // accesss.
            var scope = params.scope, me;

            // uer may have refreshed the browser, in which case retrieve current user info from session cookie
            me = ($rootScope.current_user) ? $rootScope.current_user : $cookieStore.get('current_user');

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
