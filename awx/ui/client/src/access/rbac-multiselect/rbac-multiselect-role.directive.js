/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */
export default
    [
        'CreateSelect2',
        'i18n',
        function(CreateSelect2, i18n) {
            return {
                restrict: 'E',
                scope: {
                    roles: '=',
                    model: '='
                },
                template: '<select ng-cloak class="AddPermissions-selectHide roleSelect2 form-control" ng-model="model" ng-options="role.name for role in roles track by role.id" multiple required></select>',
                link: function(scope, element, attrs, ctrl) {
                    CreateSelect2({
                        element: '.roleSelect2',
                        multiple: true,
                        placeholder: i18n._('Select roles')
                    });
                }
            };
        }
    ];
