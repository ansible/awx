/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


import { templateUrl } from '../../shared/template-url/template-url.factory';
import controller from '../../scheduler/schedulerList.controller';
import addController from '../../scheduler/schedulerAdd.controller';
import editController from '../../scheduler/schedulerEdit.controller';
import { N_ } from '../../i18n';
import editScheduleResolve from '../../scheduler/editSchedule.resolve';


export default
angular.module('managementJobScheduler', [])
    .controller('managementJobController', controller)
    .controller('managementJobAddController', addController)
    .controller('managementJobEditController', editController)
    .run(['$stateExtender', function($stateExtender) {
        $stateExtender.addState({
            searchPrefix: 'schedule',
            name: 'managementJobsList.schedule',
            route: '/management_jobs/:id/schedules',
            ncyBreadcrumb: {
                parent: 'managementJobsList',
                label: N_('SCHEDULES')
            },
            views: {
                '@managementJobsList': {
                    templateProvider: function(ScheduleList, generateList, ParentObject, $filter) {
                        // include name of parent resource in listTitle
                        ScheduleList.listTitle = `${$filter('sanitize')(ParentObject.name)}<div class='List-titleLockup'></div>` + N_('SCHEDULES');
                        let html = generateList.build({
                            list: ScheduleList,
                            mode: 'edit'
                        });
                        html = generateList.wrapPanel(html);
                        return generateList.insertFormView() + html;
                    },
                    controller: 'managementJobController',
                }
            },
            resolve: {
                Dataset: ['ScheduleList', 'QuerySet', '$stateParams', 'GetBasePath',
                    function(list, qs, $stateParams, GetBasePath) {
                        let path = `${GetBasePath('system_job_templates')}${$stateParams.id}/schedules`;
                        return qs.search(path, $stateParams[`${list.iterator}_search`]);
                    }
                ],
                ParentObject: ['$stateParams', 'Rest', 'GetBasePath', function($stateParams, Rest, GetBasePath) {
                    let path = `${GetBasePath('system_job_templates')}${$stateParams.id}`;
                    Rest.setUrl(path);
                    return Rest.get(path).then((res) => res.data);
                }],
                UnifiedJobsOptions: ['Rest', 'GetBasePath', '$stateParams', '$q',
                    function(Rest, GetBasePath, $stateParams, $q) {
                        Rest.setUrl(GetBasePath('unified_jobs'));
                        var val = $q.defer();
                        Rest.options()
                            .then(function(data) {
                                val.resolve(data.data);
                            }, function(data) {
                                val.reject(data);
                            });
                        return val.promise;
                    }],
                ScheduleList: ['SchedulesList', 'GetBasePath', '$stateParams',
                    (SchedulesList, GetBasePath, $stateParams) => {
                        let list = _.cloneDeep(SchedulesList);
                        list.basePath = GetBasePath('system_job_templates') + $stateParams.id + '/schedules';
                        return list;
                    }
                ]
            }
        });
        $stateExtender.addState({
            name: 'managementJobsList.schedule.add',
            route: '/add',
            ncyBreadcrumb: {
                parent: 'managementJobsList.schedule',
                label: N_('CREATE SCHEDULED JOB')
            },
            views: {
                'form': {
                    templateUrl: templateUrl('management-jobs/scheduler/schedulerForm'),
                    controller: 'managementJobAddController',
                }
            }
        });
        $stateExtender.addState({
            name: 'managementJobsList.schedule.edit',
            route: '/edit/:schedule_id',
            ncyBreadcrumb: {
                parent: 'managementJobsList.schedule',
                label: N_('EDIT SCHEDULED JOB')
            },
            views: {
                'form': {
                    templateUrl: templateUrl('management-jobs/scheduler/schedulerForm'),
                    controller: 'managementJobEditController'
                }
            },
            resolve: editScheduleResolve()
        });
    }]);
