/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import { N_ } from '../../i18n';

export default {
    name: 'managementJobsList.notifications',
    route: '/:management_id/notifications',
    params: {
        notification_search: {}
    },
    searchPrefix: 'notification',
    views: {
        '@managementJobsList': {
            controller: 'managementJobsNotificationsController',
            templateProvider: function(NotificationsList, generateList, ParentObject, $filter) {
                // include name of parent resource in listTitle
                NotificationsList.listTitle = `${$filter('sanitize')(ParentObject.name)}<div class='List-titleLockup'></div>` + N_('Notifications');
                let html = generateList.build({
                    list: NotificationsList,
                    mode: 'edit'
                });
                html = generateList.wrapPanel(html);
                return generateList.insertFormView() + html;
            }
        }
    },
    resolve: {
        Dataset: ['NotificationsList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = `${GetBasePath('notification_templates')}`;
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ],
        ParentObject: ['$stateParams', 'Rest', 'GetBasePath', function($stateParams, Rest, GetBasePath) {
            let path = `${GetBasePath('system_job_templates')}${$stateParams.management_id}`;
            Rest.setUrl(path);
            return Rest.get(path).then((res) => res.data);
        }],
        isAdmin: ['Rest', 'GetBasePath', function(Rest, GetBasePath) {
            Rest.setUrl(GetBasePath('me'));
            return Rest.get()
                .then((res) => {
                    if (res.data && res.data.results && res.data.count && res.data.results[0] && res.data.results[0].is_superuser) {
                        return true;
                    }
                    return false;
                })
                .catch(() => {
                    return false;
                });
        }]
    },
    ncyBreadcrumb: {
        parent: 'managementJobsList',
        label: N_('NOTIFICATIONS')
    }
};
