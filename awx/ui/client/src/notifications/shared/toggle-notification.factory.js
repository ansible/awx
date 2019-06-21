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

export default ['Wait', 'ProcessErrors', 'Rest',
    function(Wait, ProcessErrors, Rest) {
    return function(params) {
        var scope = params.scope,
            notifier = params.notifier,
            notifier_id = params.notifier.id,
            callback = params.callback,
            column = params.column, // notification_template_success/notification_template__error/notification_template_started
            url = params.url + "/" + column + '/';

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
        // Show the working spinner
        Wait('start');
        Rest.setUrl(url);
        Rest.post(params)
            .then(({data}) => {
                if (callback) {
                    scope.$emit(callback, data.id);
                    notifier[column] = !notifier[column];
                }
                // Hide the working spinner
                Wait('stop');
            })
            .catch(({data, status}) => {
                ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                    msg: 'Failed to update notification ' + data.id + ' PUT returned: ' + status });
            });
    };
}];
