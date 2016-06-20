 /*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    [   '$rootScope','Wait', 'generateList', 'NotificationTemplatesList',
        'GetBasePath' , 'SearchInit' , 'PaginateInit', 'Rest' ,
        'ProcessErrors', 'Prompt', '$state', 'GetChoices', 'Empty', 'Find',
        'ngToast', '$compile', '$filter',
        function(
            $rootScope,Wait, GenerateList, NotificationTemplatesList,
            GetBasePath, SearchInit, PaginateInit, Rest,
            ProcessErrors, Prompt, $state, GetChoices, Empty, Find, ngToast,
            $compile, $filter) {
            var scope = $rootScope.$new(),
                defaultUrl = GetBasePath('notification_templates'),
                list = NotificationTemplatesList,
                view = GenerateList;

            view.inject( list, {
                mode: 'edit',
                scope: scope
            });

            scope.removePostRefresh = scope.$on('PostRefresh', function () {
                Wait('stop');
                if (scope.notification_templates) {
                    scope.notification_templates.forEach(function(notification_template, i) {
                        scope.notification_type_options.forEach(function(type) {
                            if (type.value === notification_template.notification_type) {
                                scope.notification_templates[i].notification_type = type.label;
                                var recent_notifications = notification_template.summary_fields.recent_notifications;
                                scope.notification_templates[i].status = recent_notifications && recent_notifications.length > 0 ? recent_notifications[0].status : "none";
                            }
                        });
                    });
                }
            });

            if (scope.removeChoicesHere) {
                scope.removeChoicesHere();
            }
            scope.removeChoicesHere = scope.$on('choicesReadyNotifierList', function () {
                list.fields.notification_type.searchOptions = scope.notification_type_options;

                SearchInit({
                    scope: scope,
                    set: 'notification_templates',
                    list: list,
                    url: defaultUrl
                });

                if ($rootScope.addedItem) {
                    scope.addedItem = $rootScope.addedItem;
                    delete $rootScope.addedItem;
                }
                PaginateInit({
                    scope: scope,
                    list: list,
                    url: defaultUrl
                });

                scope.search(list.iterator);

            });

            GetChoices({
                scope: scope,
                url: defaultUrl,
                field: 'notification_type',
                variable: 'notification_type_options',
                callback: 'choicesReadyNotifierList'
            });

            function attachElem(event, html, title) {
                var elem = $(event.target).parent();
                try {
                    elem.tooltip('hide');
                    elem.popover('destroy');
                }
                catch(err) {
                    //ignore
                }

                $('.popover').each(function() {
                    // remove lingering popover <div>. Seems to be a bug in TB3 RC1
                    $(this).remove();
                });
                $('.tooltip').each( function() {
                    // close any lingering tool tipss
                    $(this).hide();
                });
                elem.attr({
                    "aw-pop-over": html,
                    "data-popover-title": title,
                    "data-placement": "right" });
                $compile(elem)(scope);
                elem.on('shown.bs.popover', function() {
                    $('.popover').each(function() {
                        $compile($(this))(scope);  //make nested directives work!
                    });
                    $('.popover-content, .popover-title').click(function() {
                        elem.popover('hide');
                    });
                });
                elem.popover('show');
            }

            scope.showSummary = function(event, id) {
                setTimeout(function(){
                    if (!Empty(id)) {
                        var recent_notifications,
                        html, title = "Recent Notifications";

                        scope.notification_templates.forEach(function(notification_template){
                            if(notification_template.id === id){
                                recent_notifications = notification_template.summary_fields.recent_notifications;
                            }
                        });
                        if (recent_notifications.length > 0) {
                            html = "<table class=\"table table-condensed flyout\" style=\"width: 100%\">\n";
                            html += "<thead>\n";
                            html += "<tr>";
                            html += "<th>Status</th>";
                            html += "<th>Time</th>";
                            html += "</tr>\n";
                            html += "</thead>\n";
                            html += "<tbody>\n";

                            recent_notifications.forEach(function(row) {
                                html += "<tr>\n";
                                html += "<td><i class=\"fa icon-job-" + row.status + "\"></i></td>\n";
                                html += "<td>" + ($filter('longDate')(row.created)).replace(/ /,'<br />') + "</td>\n";
                                html += "</tr>\n";
                            });
                            html += "</tbody>\n";
                            html += "</table>\n";
                        }
                        else {
                            html = "<p>No recent notifications.</p>\n";
                        }
                        attachElem(event, html, title);
                    }
                }, 100);
            };

            scope.testNotification = function(){
                var name = this.notification_template.name;
                Rest.setUrl(defaultUrl + this.notification_template.id +'/test/');
                Rest.post({})
                    .then(function (data) {
                        if(data && data.data && data.data.notification){
                            Wait('start');
                            // Using a setTimeout here to wait for the
                            // notification to be processed and for a status
                            // to be returned from the API.
                            setTimeout(function(){
                                var id = data.data.notification,
                                url = GetBasePath('notifications') + id;
                                Rest.setUrl(url);
                                Rest.get()
                                .then(function (res) {
                                    Wait('stop');
                                    if(res && res.data && res.data.status && res.data.status === "successful"){
                                        scope.search(list.iterator);
                                        ngToast.success({
                                            content: `<i class="fa fa-check-circle Toast-successIcon"></i> <b>${name}:</b> Notification sent.`
                                        });
                                    }
                                    else if(res && res.data && res.data.status && res.data.status === "failed"){
                                        scope.search(list.iterator);
                                        ngToast.danger({
                                            content: `<i class="fa fa-exclamation-triangle Toast-successIcon"></i> <b>${name}:</b> Notification failed.`
                                        });
                                    }
                                    else {
                                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                            msg: 'Call to ' + url + ' failed. Notification returned status: ' + status });
                                    }
                                });
                            } , 5000);
                    }
                    else {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to notifcatin templates failed. Notification returned status: ' + status });
                    }
                })
                .catch(function () {
                    ngToast.danger({
                        content: `<i class="fa fa-check-circle Toast-successIcon"></i> <b>${name}:</b> Notification Failed.`,
                     });
                });
            };

            scope.addNotification = function(){
                $state.transitionTo('notifications.add');
            };

            scope.editNotification = function(){
                $state.transitionTo('notifications.edit',{
                    notification_template_id: this.notification_template.id,
                    notification_template: this.notification_templates
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
                            if (parseInt($state.params.notification_template_id) === id) {
                                $state.go("^", null, {reload: true});
                            } else {
                                scope.search(list.iterator);
                            }
                        })
                        .error(function (data, status) {
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                        });
                };
                var bodyHtml = '<div class="Prompt-bodyQuery">Are you sure you want to delete the notification template below?</div><div class="Prompt-bodyTarget">' + name + '</div>';
                Prompt({
                    hdr: 'Delete',
                    body: bodyHtml,
                    action: action,
                    actionText: 'DELETE'
                });
            };
        }
    ];
