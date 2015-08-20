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
            // [{name: "read", value: "Read Inventory"}, ...]
            return params.choices.filter(function (kvp) {
                return (kvp[0] !== "adhoc");
            }).map(function (kvp) {
                if (kvp[0] !== "adhoc") {
                    return {name: kvp[1], value: kvp[0]};
                }
            });
        };
    }];
