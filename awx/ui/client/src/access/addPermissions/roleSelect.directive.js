/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */
export default
    [
        'CreateSelect2',
        function(CreateSelect2) {
            return {
                restrict: 'E',
                scope: false,
                template: '<select ng-cloak class="AddPermissions-selectHide roleSelect2 form-control" ng-model="obj.roles" ng-options="role.label for role in roles | filter:{label: \'!Read\'} track by role.value" multiple required></select>',
                link: function(scope, element, attrs, ctrl) {
                    CreateSelect2({
                        element: '.roleSelect2',
                        multiple: true,
                        placeholder: 'Select roles'
                    });
                }
            };
        }
    ];
