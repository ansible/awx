 /*************************************************
  * Copyright (c) 2015 Ansible, Inc.
  *
  * All Rights Reserved
  *************************************************/

 export default ['$scope', 'Wait', 'NotificationTemplatesList',
     'GetBasePath', 'Rest', 'ProcessErrors', 'Prompt', '$state',
     'ngToast', '$filter', 'Dataset', 'rbacUiControlService',
     'i18n', 'NotificationTemplate', 'AppStrings',
     function(
         $scope, Wait, NotificationTemplatesList,
         GetBasePath, Rest, ProcessErrors, Prompt, $state,
         ngToast, $filter, Dataset, rbacUiControlService,
         i18n, NotificationTemplate, AppStrings) {

         var defaultUrl = GetBasePath('notification_templates'),
             list = NotificationTemplatesList;

         init();

         function init() {
             $scope.canAdd = false;

             rbacUiControlService.canAdd("notification_templates")
                 .then(function(params) {
                     $scope.canAdd = params.canAdd;
                 });

             // search init
             $scope.list = list;
             $scope[`${list.iterator}_dataset`] = Dataset.data;
             $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
        }

             $scope.$on(`notification_template_options`, function(event, data){
                 $scope.options = data.data.actions.GET;
                 optionsRequestDataProcessing();
             });

             $scope.$watchCollection("notification_templates", function() {
                    optionsRequestDataProcessing();
                 }
             );
             // iterate over the list and add fields like type label, after the
             // OPTIONS request returns, or the list is sorted/paginated/searched.
             function optionsRequestDataProcessing(){
                 $scope[list.name].forEach(function(item, item_idx) {
                     var itm = $scope[list.name][item_idx];
                     // Set the item type label
                     if (list.fields.notification_type && $scope.options &&
                         $scope.options.hasOwnProperty('notification_type')) {
                             $scope.options.notification_type.choices.forEach(function(choice) {
                                 if (choice[0] === item.notification_type) {
                                     itm.type_label = choice[1];
                                     var recent_notifications = itm.summary_fields.recent_notifications;
                                     itm.status = recent_notifications && recent_notifications.length > 0 ? recent_notifications[0].status : "none";
                                 }
                             });
                     }
                     setStatus(itm);
                 });
             }

         function setStatus(notification_template) {
             var html, recent_notifications = notification_template.summary_fields.recent_notifications;
             if (recent_notifications.length > 0) {
                 html = "<table class=\"table table-condensed flyout\" style=\"width: 100%\">\n";
                 html += "<thead>\n";
                 html += "<tr>";
                 html += "<th>" + i18n._("Status") + "</th>";
                 html += "<th>" + i18n._("Time") + "</th>";
                 html += "</tr>\n";
                 html += "</thead>\n";
                 html += "<tbody>\n";

                 recent_notifications.forEach(function(row) {
                     html += "<tr>\n";
                     html += `<td><i class=\"SmartStatus-tooltip--${row.status} fa icon-job-${row.status}"></i></td>`;
                     html += "<td>" + ($filter('longDate')(row.created)).replace(/ /, '<br />') + "</td>\n";
                     html += "</tr>\n";
                 });
                 html += "</tbody>\n";
                 html += "</table>\n";
             } else {
                 html = "<p>" + i18n._("No recent notifications.") + "</p>\n";
             }
             notification_template.template_status_html = html;
         }

        $scope.copyNotification = notificationTemplate => {
            Wait('start');
            new NotificationTemplate('get', notificationTemplate.id)
                .then(model => model.copy())
                .then((copiedNotification) => {
                    ngToast.success({
                        content: `
                            <div class="Toast-wrapper">
                                <div class="Toast-icon">
                                    <i class="fa fa-check-circle Toast-successIcon"></i>
                                </div>
                                <div>
                                    ${AppStrings.get('SUCCESSFUL_CREATION', copiedNotification.name)}
                                </div>
                            </div>`,
                        dismissButton: false,
                        dismissOnTimeout: true
                    });
                    $state.go('.', null, { reload: true });
                })
                .catch(({ data, status }) => {
                    const params = { hdr: 'Error!', msg: `Call to copy failed. Return status: ${status}` };
                    ProcessErrors($scope, data, status, null, params);
                })
                .finally(() => Wait('stop'));
        };

         $scope.testNotification = function() {
             var name = $filter('sanitize')(this.notification_template.name),
                 pending_retries = 25;

             Rest.setUrl(defaultUrl + this.notification_template.id + '/test/');
             Rest.post({})
                 .then(function(data) {
                     if (data && data.data && data.data.notification) {
                         Wait('start');
                         // Using a setTimeout here to wait for the
                         // notification to be processed and for a status
                         // to be returned from the API.
                         retrieveStatus(data.data.notification);
                     } else {
                         ProcessErrors($scope, data, status, null, {
                             hdr: 'Error!',
                             msg: 'Call to notification templates failed. Notification returned status: ' + status
                         });
                     }
                 })
                 .catch(function() {
                     ngToast.danger({
                         content: `<i class="fa fa-check-circle Toast-successIcon"></i> <b>${name}:</b> ` + i18n._('Notification Failed.'),
                     });
                 });

             function retrieveStatus(id) {
                 setTimeout(function() {
                     let url = GetBasePath('notifications') + id;
                     Rest.setUrl(url);
                     Rest.get()
                         .then(function(res) {
                             if (res && res.data && res.data.status && res.data.status === "successful") {
                                 ngToast.success({
                                     content: `<i class="fa fa-check-circle Toast-successIcon"></i> <b>${name}:</b> Notification sent.`
                                 });
                                 $state.reload();
                             } else if (res && res.data && res.data.status && res.data.status === "failed" && res.data.error === "timed out") {
                                 ngToast.danger({
                                     content: `<div><i class="fa fa-exclamation-triangle Toast-successIcon"></i> <b>${name}:</b> ${i18n._("Notification timed out.")}</div>`
                                 });
                                 $state.reload();
                             } else if (res && res.data && res.data.status && res.data.status === "failed") {
                                 ngToast.danger({
                                     content: `<div><i class="fa fa-exclamation-triangle Toast-successIcon"></i> <b>${name}:</b> Notification failed.</div><div>${$filter('sanitize')(res.data.error)}</div>`
                                 });
                                 $state.reload();
                             } else if (res && res.data && res.data.status && res.data.status === "pending" && pending_retries > 0) {
                                 pending_retries--;
                                 retrieveStatus(id);
                             } else {
                                 Wait('stop');
                                 ProcessErrors($scope, null, status, null, {
                                     hdr: 'Error!',
                                     msg: 'Call to test notifications failed.'
                                 });
                             }

                         })
                         .catch(({data, status}) => {
                            ProcessErrors($scope, data, status, null, {
                                hdr: 'Error!',
                                msg: 'Failed to get ' + url + '. GET status: ' + status
                            });
                        });
                 }, 5000);
             }
         };


         $scope.addNotification = function() {
             $state.go('notifications.add');
         };

         $scope.editNotification = function() {
             $state.go('notifications.edit', {
                 notification_template_id: this.notification_template.id,
                 notification_template: this.notification_templates
             });
         };

         $scope.deleteNotification = function(id, name) {
             var action = function() {
                 $('#prompt-modal').modal('hide');
                 Wait('start');
                 var url = defaultUrl + id + '/';
                 Rest.setUrl(url);
                 Rest.destroy()
                     .then(() => {

                         let reloadListStateParams = null;

                         if($scope.notification_templates.length === 1 && $state.params.notification_template_search && _.has($state, 'params.notification_template_search.page') && $state.params.notification_template_search.page !== '1') {
                             reloadListStateParams = _.cloneDeep($state.params);
                             reloadListStateParams.notification_template_search.page = (parseInt(reloadListStateParams.notification_template_search.page)-1).toString();
                         }

                         if (parseInt($state.params.notification_template_id) === id) {
                            $state.go("^", reloadListStateParams, { reload: true });
                         } else {
                            $state.go('.', reloadListStateParams, {reload: true});
                         }
                         Wait('stop');
                     })
                     .catch(({data, status}) => {
                         ProcessErrors($scope, data, status, null, {
                             hdr: 'Error!',
                             msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status
                         });
                     });
             };

             Prompt({
                 hdr: i18n._('Delete'),
                 resourceName: $filter('sanitize')(name),
                 body: '<div class="Prompt-bodyQuery">' + i18n._('Are you sure you want to delete this notification template?') + '</div>',
                 action: action,
                 actionText: i18n._('DELETE')
             });
         };
     }
 ];
