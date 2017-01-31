/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 /**
 * @ngdoc function
 * @name helpers.function:ActivityStream
 * @description Helper functions for the activity stream
*/

export default
    angular.module('ActivityStreamHelper', ['Utilities'])
        .factory('GetTargetTitle', ['i18n',
            function (i18n) {
                return function (target) {

                    var rtnTitle = i18n._('ALL ACTIVITY');

                    switch(target) {
                        case 'project':
                            rtnTitle = i18n._('PROJECTS');
                            break;
                        case 'inventory':
                            rtnTitle = i18n._('INVENTORIES');
                            break;
                        case 'credential':
                            rtnTitle = i18n._('CREDENTIALS');
                            break;
                        case 'user':
                            rtnTitle = i18n._('USERS');
                            break;
                        case 'team':
                            rtnTitle = i18n._('TEAMS');
                            break;
                        case 'organization':
                            rtnTitle = i18n._('ORGANIZATIONS');
                            break;
                        case 'job':
                            rtnTitle = i18n._('JOBS');
                            break;
                        case 'inventory_script':
                            rtnTitle = i18n._('INVENTORY SCRIPTS');
                            break;
                        case 'schedule':
                            rtnTitle = i18n._('SCHEDULES');
                            break;
                        case 'host':
                            rtnTitle = i18n._('HOSTS');
                            break;
                        case 'template':
                            rtnTitle = i18n._('TEMPLATES');
                            break;
                    }

                    return rtnTitle;

                };
            }
        ]);
