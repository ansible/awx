/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    [   'NotificationsList', 'GetBasePath', 'ToggleNotification', 'NotificationsListInit',
        '$stateParams', 'Dataset', '$scope',
        function(
            NotificationsList, GetBasePath, ToggleNotification, NotificationsListInit,
            $stateParams, Dataset, $scope) {
            var defaultUrl = GetBasePath('system_job_templates'),
                list = NotificationsList,
                id = $stateParams.management_id;

            function init() {
                $scope.list = list;
                $scope[`${list.iterator}_dataset`] = Dataset.data;
                $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

                NotificationsListInit({
                    scope: $scope,
                    url: defaultUrl,
                    id: id
                });

                $scope.$watch(`${list.iterator}_dataset`, function() {
                    // The list data has changed and we need to update which notifications are on/off
                    $scope.$emit('relatednotifications');
                });
            }

            $scope.toggleNotification = function(event, notifier_id, column) {
                var notifier = this.notification;
                try {
                    $(event.target).tooltip('hide');
                }
                catch(e) {
                    // ignore
                }
                ToggleNotification({
                    scope: $scope,
                    url: defaultUrl + id,
                    notifier: notifier,
                    column: column,
                    callback: 'NotificationRefresh'
                });
            };

            init();

        }
    ];
