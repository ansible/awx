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
            // {name: "read", value: "Read Inventory", ...}
            return params.choices.reduce(function(obj, kvp) {
                // for now, remove adhoc from those choices
                if (kvp[0] !== adhoc) {
                    return {name: kvp[0], value: kvp[1]};
                } else {
                    return null;
                }
            }, {});
        };
    }];
