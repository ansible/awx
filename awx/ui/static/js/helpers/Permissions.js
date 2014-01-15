/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Permissions.js
 *
 *  Functions shared amongst Permission related controllers
 *
 */
angular.module('PermissionsHelper', [])  
    
    // Handle category change event
    .factory('PermissionCategoryChange', [ function() {
    return function(params) {
        var scope = params.scope;
        var reset = params.reset; 

        if (scope.category == 'Inventory') {
            scope.projectrequired = false;
            scope.permissionTypeHelp = 
                "<dl>\n" + 
                "<dt>Read</dt>\n" +
                "<dd>Only allow the user or team to view the inventory.</dd>\n" +
                "<dt>Write</dt>\n" + 
                "<dd>Allow the user or team to modify hosts and groups contained in the inventory, add new hosts and groups, and perform inventory sync operations.\n" +
                "<dt>Admin</dt>\n" +
                "<dd>Allow the user or team full access to the inventory. This includes reading, writing, deletion of the inventory and inventory sync operations.</dd>\n" +
                "</dl>\n";
        }
        else {
            scope.projectrequired = true;
            scope.permissionTypeHelp = 
                "<dl>\n" + 
                "<dt>Run</dt>\n" +
                "<dd>Allow the user or team to perform a live deployment of the project against the inventory. In Run mode modules will " +
                "be executed, and changes to the inventory will occur.</dd>\n" +
                "<dt>Check</dt>\n" +
                "<dd>Only allow the user or team to deploy the project against the inventory as a dry-run operation. In Check mode, module operations " +
                "will only be simulated. No changes will occur.</dd>\n" +
                "</dl>\n";
        }

        if (reset) {
            scope.permission_type = (scope.category == 'Inventory') ? 'read' : 'run';  //default to the first option
        }
         
        }
        }]);
      