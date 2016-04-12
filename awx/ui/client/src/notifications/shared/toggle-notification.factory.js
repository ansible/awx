/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
/**
 * Flip a notifications's enable flag
 *
 * ToggleNotification({
 *     scope:       scope,
 *     id:          schedule.id to update
 *     callback:    scope.$emit label to call when update completes
 * });
 *
 */

export default ['Wait', 'GetBasePath', 'ProcessErrors', 'Rest',
    function(Wait, GetBasePath, ProcessErrors, Rest) {
    return function(params) {
        var scope = params.scope,
            notifier = params.notifier,
            id = params.id,
            notifier_id = params.notifier.id,
            callback = params.callback,
            column = params.column, // notifiers_success/notifiers_error
            url = params.url+ id+ "/"+ column + '/';

        if(!notifier[column]){
            params = {
                id: notifier_id
            };
        }
        else {
            params = {
                id: notifier_id,
                disassociate: 1
            };
        }
        Rest.setUrl(url);
        Rest.post(params)
            .success( function(data) {
                if (callback) {
                    scope.$emit(callback, data.id);
                    notifier[column] = !notifier[column];
                }
                else {
                    Wait('stop');
                }
            })
            .error( function(data, status) {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Failed to update notification ' + data.id + ' PUT returned: ' + status });
            });
    };
}];
