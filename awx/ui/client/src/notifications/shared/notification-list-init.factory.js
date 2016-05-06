/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
/**
 * For setting the values and choices for notification lists
 *
 * NotificationsListInit({
 *     scope:       scope,
 *     id:          notification.id to update
 *     url:         notifier url off of related object
 * });
 *
 */

export default ['Wait', 'GetBasePath', 'ProcessErrors', 'Rest',
    function(Wait, GetBasePath, ProcessErrors, Rest) {
    return function(params) {
        var scope = params.scope,
            url = params.url,
            id = params.id;

        if (scope.relatednotificationsRemove) {
            scope.relatednotificationsRemove();
        }
        scope.relatednotificationsRemove = scope.$on('relatednotifications', function () {
                var columns = ['/notification_templates_success/', '/notification_templates_error/'];

                _.map(columns, function(column){
                    var notifier_url = url + id + column;
                    Rest.setUrl(notifier_url);
                    Rest.get()
                        .success( function(data, i, j, obj) {
                            var type = (obj.url.indexOf('success')>0) ? "notification_templates_success" : "notification_templates_error";
                            if (data.results) {
                                    _.forEach(data.results, function(result){
                                        _.forEach(scope.notifications, function(notification){
                                            if(notification.id === result.id){
                                                notification[type] = true;
                                            }
                                        });
                                    });
                            }
                            else {
                                Wait('stop');
                            }
                        })
                        .error( function(data, status) {
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'Failed to update notification ' + data.id + ' PUT returned: ' + status });
                        });
                });

        });
    };
}];
