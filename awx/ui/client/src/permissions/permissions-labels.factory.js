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
    ['Rest', 'ProcessErrors', function(Rest, ProcessErrors) {
        return function (params) {
            var scope = params.scope,
                url = params.url;

            // Auto populate the field if there is only one result
            Rest.setUrl(url);
            return Rest.options()
                .then(function (data) {
                    data = data.data;
                    var choices = data.actions.GET.permission_type.choices;

                    // convert the choices from the API from the format
                    // [["read", "Read Inventory"], ...] to
                    // {read: "Read Inventory", ...}
                    choices = choices.reduce(function(obj, kvp) {
                        obj[kvp[0]] = kvp[1];
                        return obj;
                    }, {});

                    // manually add the adhoc label to the choices object
                    choices['adhoc'] = data.actions.GET.run_ad_hoc_commands.label;

                    return choices;
                })
                .catch(function (data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to get permission type labels. Options requrest returned status: ' + status });
                });
        };
    }];
