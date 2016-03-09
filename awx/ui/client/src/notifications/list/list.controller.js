/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    [   '$rootScope','Wait', 'generateList', 'notificationsListObject',
        'GetBasePath' , 'SearchInit' , 'PaginateInit',
        'Rest' , 'ProcessErrors', 'Prompt', '$state',
        function(
            $rootScope,Wait, GenerateList, notificationsListObject,
            GetBasePath, SearchInit, PaginateInit,
            Rest, ProcessErrors, Prompt, $state
        ) {
            var scope = $rootScope.$new(),
                defaultUrl = GetBasePath('notifications'),
                list = notificationsListObject,
                view = GenerateList;

            view.inject( list, {
                mode: 'edit',
                scope: scope
            });

            // SearchInit({
            //     scope: scope,
            //     set: 'notifications',
            //     list: list,
            //     url: defaultUrl
            // });
            //
            // if ($rootScope.addedItem) {
            //     scope.addedItem = $rootScope.addedItem;
            //     delete $rootScope.addedItem;
            // }
            // PaginateInit({
            //     scope: scope,
            //     list: list,
            //     url: defaultUrl
            // });
            //
            // scope.search(list.iterator);

            scope.editNotification = function(){
                $state.transitionTo('notifications.edit',{
                    inventory_script_id: this.inventory_script.id,
                    inventory_script: this.inventory_script
                });
            };

            scope.deleteNotification =  function(id, name){

                var action = function () {
                    $('#prompt-modal').modal('hide');
                    Wait('start');
                    var url = defaultUrl + id + '/';
                    Rest.setUrl(url);
                    Rest.destroy()
                        .success(function () {
                            scope.search(list.iterator);
                        })
                        .error(function (data, status) {
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                        });
                };

                var bodyHtml = '<div class="Prompt-bodyQuery">Are you sure you want to delete the inventory script below?</div><div class="Prompt-bodyTarget">' + name + '</div>';
                Prompt({
                    hdr: 'Delete',
                    body: bodyHtml,
                    action: action,
                    actionText: 'DELETE'
                });
            };

            scope.addNotification = function(){
                $state.transitionTo('notifications.add');
            };

        }
    ];
