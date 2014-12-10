/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Permissions.js
 */
    /**
 * @ngdoc function
 * @name helpers.function:Permissions
 * @description
 *  Functions shared amongst Permission related controllers
 *
 */
angular.module('PermissionsHelper', [])

// Handle category change event
.factory('PermissionCategoryChange', ['$sce',
    function ($sce) {
        return function (params) {
            var scope = params.scope,
                reset = params.reset,
                html;

            if (scope.category === 'Inventory') {
                scope.projectrequired = false;
                html = "<dl>\n" +
                    "<dt>Read</dt>\n" +
                    "<dd>Only allow the user or team to view the inventory.</dd>\n" +
                    "<dt>Write</dt>\n" +
                    "<dd>Allow the user or team to modify hosts and groups contained in the inventory, add new hosts and groups, and perform inventory sync operations.\n" +
                    "<dt>Admin</dt>\n" +
                    "<dd>Allow the user or team full access to the inventory. This includes reading, writing, deletion of the inventory and inventory sync operations.</dd>\n" +
                    "</dl>\n";
                scope.permissionTypeHelp = $sce.trustAsHtml(html);
            } else {
                scope.projectrequired = true;
                html = "<dl>\n" +
		    "<dt>Create</dt>\n" +
		    "<dd>Allow the user or team to create job templates. This implies that they have the Run and Check permissions.</dd>\n" +
                    "<dt>Run</dt>\n" +
                    "<dd>Allow the user or team to run a job template from the project against the inventory. In Run mode modules will " +
                    "be executed, and changes to the inventory will occur.</dd>\n" +
                    "<dt>Check</dt>\n" +
                    "<dd>Only allow the user or team to run the project against the inventory as a dry-run operation. In Check mode, module operations " +
                    "will only be simulated. No changes will occur.</dd>\n" +
                    "</dl>\n";
                scope.permissionTypeHelp = $sce.trustAsHtml(html);
            }

            if (reset) {
                scope.permission_type = (scope.category === 'Inventory') ? 'read' : 'run'; //default to the first option
            }
        };
    }
]);
