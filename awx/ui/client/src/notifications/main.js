/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


import notificationTemplatesList from './notification-templates-list/main';
import notificationsAdd from './add/main';
import notificationsEdit from './edit/main';

import list from './notificationTemplates.list';
import form from './notificationTemplates.form';
import notificationsList from './notifications.list';
import toggleNotification from './shared/toggle-notification.factory';
import notificationsListInit from './shared/notification-list-init.factory';
import typeChange from './shared/type-change.service';
import messageUtils from './shared/message-utils.service';
import { N_ } from '../i18n';

export default
angular.module('notifications', [
        notificationTemplatesList.name,
        notificationsAdd.name,
        notificationsEdit.name
    ])
    .factory('NotificationTemplatesList', list)
    .factory('NotificationsFormObject', form)
    .factory('NotificationsList', notificationsList)
    .factory('ToggleNotification', toggleNotification)
    .factory('NotificationsListInit', notificationsListInit)
    .service('NotificationsTypeChange', typeChange)
    .service('MessageUtils', messageUtils)
    .config(['$stateProvider', 'stateDefinitionsProvider',
        function($stateProvider, stateDefinitionsProvider) {
            let stateDefinitions = stateDefinitionsProvider.$get();

            // lazily generate a tree of substates which will replace this node in ui-router's stateRegistry
            // see: stateDefinition.factory for usage documentation
            $stateProvider.state({
                name: 'notifications.**',
                url: '/notification_templates',
                ncyBreadcrumb: {
                    label: N_("NOTIFICATIONS")
                },
                lazyLoad: () => stateDefinitions.generateTree({
                    parent: 'notifications', // top-most node in the generated tree
                    modes: ['add', 'edit'], // form nodes to generate
                    list: 'NotificationTemplatesList',
                    form: 'NotificationsFormObject',
                    controllers: {
                        list: 'notificationTemplatesListController',
                        add: 'notificationsAddController',
                        edit: 'notificationsEditController'
                    },
                    urls: {
                        add: '/add?organization_id'
                    },
                    resolve: {
                        edit: {
                            notification_template: ['$state', '$stateParams', '$q',
                                'Rest', 'GetBasePath', 'ProcessErrors',
                                function($state, $stateParams, $q, rest, getBasePath, ProcessErrors) {
                                    if ($stateParams.notification_template) {
                                        return $q.when($stateParams.notification_template);
                                    }

                                    var notificationTemplateId = $stateParams.notification_template_id;

                                    var url = getBasePath('notification_templates') + notificationTemplateId + '/';
                                    rest.setUrl(url);
                                    return rest.get()
                                        .then(function(res) {
                                            if (_.get(res, ['data', 'notification_type'] === 'webhook') &&
                                                _.get(res, ['data', 'notification_configuration', 'http_method'])) {
                                                res.data.notification_configuration.http_method = res.data.notification_configuration.http_method.toUpperCase();
                                            }
                                            return res.data;
                                        }).catch(function(response) {
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: 'Error!',
                                                msg: 'Failed to get inventory script info. GET returned status: ' +
                                                    response.status
                                            });
                                        });
                                }
                            ]
                        }
                    },
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'notification_template'
                    },
                    ncyBreadcrumb: {
                        label: N_('NOTIFICATIONS')
                    }
                })
            });
        }
    ]);
