/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


import { templateUrl } from '../../shared/template-url/template-url.factory';
import controller from '../../scheduler/schedulerList.controller';
import addController from '../../scheduler/schedulerAdd.controller';
import editController from '../../scheduler/schedulerEdit.controller';

export default
angular.module('managementJobScheduler', [])
    .controller('managementJobController', controller)
    .controller('managementJobAddController', addController)
    .controller('managementJobEditController', editController)
    .run(['$stateExtender', function($stateExtender) {
        $stateExtender.addState({
            searchPrefix: 'schedule',
            name: 'managementJobSchedules',
            route: '/management_jobs/:id/schedules',
            ncyBreadcrumb: {
                parent: 'managementJobsList',
                label: 'SCHEDULES'
            },
            views: {
                '@': {
                    templateProvider: function(SchedulesList, generateList, ParentObject) {
                        // include name of parent resource in listTitle
                        SchedulesList.listTitle = `${ParentObject.name}<div class='List-titleLockup'></div>Schedules`;
                        let html = generateList.build({
                            list: SchedulesList,
                            mode: 'edit'
                        });
                        html = generateList.wrapPanel(html);
                        return generateList.insertFormView() + html;
                    },
                    controller: 'managementJobController',
                }
            },
            resolve: {
                Dataset: ['SchedulesList', 'QuerySet', '$stateParams', 'GetBasePath',
                    function(list, qs, $stateParams, GetBasePath) {
                        let path = `${GetBasePath('system_job_templates')}${$stateParams.id}/schedules`;
                        return qs.search(path, $stateParams[`${list.iterator}_search`]);
                    }
                ],
                ParentObject: ['$stateParams', 'Rest', 'GetBasePath', function($stateParams, Rest, GetBasePath) {
                    let path = `${GetBasePath('system_job_templates')}${$stateParams.id}`;
                    Rest.setUrl(path);
                    return Rest.get(path).then((res) => res.data);
                }]
            }
        });
        $stateExtender.addState({
            name: 'managementJobSchedules.add',
            route: '/add',
            ncyBreadcrumb: {
                parent: 'managementJobSchedules',
                label: 'CREATE SCHEDULED JOB'
            },
            views: {
                'form': {
                    templateUrl: templateUrl('management-jobs/scheduler/schedulerForm'),
                    controller: 'managementJobAddController',
                }
            }
        });
        $stateExtender.addState({
            name: 'managementJobSchedules.edit',
            route: '/edit/:schedule_id',
            ncyBreadcrumb: {
                parent: 'managementJobSchedules',
                label: 'EDIT SCHEDULED JOB'
            },
            views: {
                'form': {
                    templateUrl: templateUrl('management-jobs/scheduler/schedulerForm'),
                    controller: 'managementJobEditController'
                }
            }
        });
    }]);
