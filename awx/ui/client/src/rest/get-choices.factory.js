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
                url = params.url,
                field = params.field,
                options = params.options;

            if (!options) {
              // Auto populate the field if there is only one result
              Rest.setUrl(url);
              return Rest.options()
                  .then(function (data) {
                      data = data.data;
                      var choices = data.actions.GET[field].choices;

                      // manually add the adhoc label to the choices object if
                      // the permission_type field
                      if (field === "permission_type") {
                          choices.push(["adhoc",
                              data.actions.GET.run_ad_hoc_commands.help_text]);
                      }

                      return choices;
                  })
                  .catch(function (data, status) {
                      ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                              msg: 'Failed to get ' + field + ' labels. Options requrest returned status: ' + status });
                  });
            } else {
              var choices = options.actions.GET[field].choices;

              // manually add the adhoc label to the choices object if
              // the permission_type field
              if (field === "permission_type") {
                  choices.push(["adhoc",
                      options.actions.GET.run_ad_hoc_commands.help_text]);
              }

              return choices;
            }
        };
    }];
