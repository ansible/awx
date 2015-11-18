/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

    /**
 * @ngdoc function
 * @name helpers.function:Permissions
 * @description
 *  Gets permission type labels from the API and sets them as the permissions labels on the relevant radio buttons
 *
 */

 export default
    [function() {
        return function (params) {
            // convert the choices from the API from the format
            // [["read", "Read Inventory"], ...] to
            // {read: "Read Inventory", ...}
            return params.choices.reduce(function(obj, kvp) {
                obj[kvp[0]] = kvp[1];
                return obj;
            }, {});
        };
    }];
