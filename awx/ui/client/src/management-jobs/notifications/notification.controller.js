/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    [   '$rootScope','Wait', 'generateList', 'NotificationsList',
        'GetBasePath' , 'SearchInit' , 'PaginateInit', 'Rest' ,
        'ProcessErrors', 'Prompt', '$state', 'GetChoices', 'Empty', 'Find',
        'ngToast', '$compile', '$filter','ToggleNotification',
        'NotificationsListInit', '$stateParams', 'management_job',
        function(
            $rootScope,Wait, GenerateList, NotificationsList,
            GetBasePath, SearchInit, PaginateInit, Rest,
            ProcessErrors, Prompt, $state, GetChoices, Empty, Find, ngToast,
            $compile, $filter, ToggleNotification, NotificationsListInit,
            $stateParams, management_job) {
            var scope = $rootScope.$new(),
                url = GetBasePath('notification_templates'),
                defaultUrl = GetBasePath('system_job_templates'),
                list = NotificationsList,
                view = GenerateList,
                id = $stateParams.management_id;

            list.listTitle = `${management_job.name} <div class="List-titleLockup"></div> Notifications`;
            view.inject( list, {
                mode: 'edit',
                cancelButton: true,
                scope: scope
            });

            NotificationsListInit({
                scope: scope,
                url: defaultUrl,
                id: id
            });

            scope.formCancel = function() {
                $state.go('managementJobsList');
            };

            scope.toggleNotification = function(event, notifier_id, column) {
                var notifier = this.notification;
                try {
                    $(event.target).tooltip('hide');
                }
                catch(e) {
                    // ignore
                }
                ToggleNotification({
                    scope: scope,
                    url: defaultUrl,
                    id: id,
                    notifier: notifier,
                    column: column,
                    callback: 'NotificationRefresh'
                });
            };

            if (scope.removePostRefresh) {
                scope.removePostRefresh();
            }
            scope.removePostRefresh = scope.$on('PostRefresh', function () {
                scope.$emit('relatednotifications');
            });

            if (scope.removeChoicesHere) {
                scope.removeChoicesHere();
            }
            scope.removeChoicesHere = scope.$on('choicesReadyNotifierList', function () {
                list.fields.notification_type.searchOptions = scope.notification_type_options;

                SearchInit({
                    scope: scope,
                    set: 'notifications',
                    list: list,
                    url: url
                });

                if ($rootScope.addedItem) {
                    scope.addedItem = $rootScope.addedItem;
                    delete $rootScope.addedItem;
                }
                PaginateInit({
                    scope: scope,
                    list: list,
                    url: url
                });

                scope.search(list.iterator);

            });

            GetChoices({
                scope: scope,
                url: url,
                field: 'notification_type',
                variable: 'notification_type_options',
                callback: 'choicesReadyNotifierList'
            });


        }
    ];
