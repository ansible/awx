/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import listController from './schedulerList.controller';
import addController from './schedulerAdd.controller';
import editController from './schedulerEdit.controller';
import {templateUrl} from '../shared/template-url/template-url.factory';
import schedulerDatePicker from './schedulerDatePicker.directive';
import { N_ } from '../i18n';
import AddSchedule from './factories/add-schedule.factory';
import DeleteSchedule from './factories/delete-schedule.factory';
import EditSchedule from './factories/edit-schedule.factory';
import RRuleToAPI from './factories/r-rule-to-api.factory';
import SchedulePost from './factories/schedule-post.factory';
import ToggleSchedule from './factories/toggle-schedule.factory';
import SchedulesList from './schedules.list';
import ScheduledJobsList from './scheduled-jobs.list';

export default
    angular.module('scheduler', [])
        .controller('schedulerListController', listController)
        .controller('schedulerAddController', addController)
        .controller('schedulerEditController', editController)
        .factory('AddSchedule', AddSchedule)
        .factory('DeleteSchedule', DeleteSchedule)
        .factory('EditSchedule', EditSchedule)
        .factory('RRuleToAPI', RRuleToAPI)
        .factory('SchedulePost', SchedulePost)
        .factory('ToggleSchedule', ToggleSchedule)
        .factory('SchedulesList', SchedulesList)
        .factory('ScheduledJobsList', ScheduledJobsList)
        .directive('schedulerDatePicker', schedulerDatePicker)
        .run(['$stateExtender', function($stateExtender) {
            // Inventory sync schedule states registered in: awx/ui/client/src/inventories/manage/groups/main.js
            // Scheduled jobs states registered in awx/uiclient/src/job-detail/main.js

            // job templates
            $stateExtender.addState({
                searchPrefix: 'schedule',
                name: 'jobTemplateSchedules',
                route: '/templates/job_template/:id/schedules',
                data: {
                    activityStream: true,
                    activityStreamTarget: 'job_template',
                    activityStreamId: 'id'
                },
                ncyBreadcrumb: {
                    parent: 'templates.editJobTemplate({job_template_id: parentObject.id})',
                    label: N_('SCHEDULES')
                },
                resolve: {
                    Dataset: ['ScheduleList', 'QuerySet', '$stateParams', 'GetBasePath',
                        function(list, qs, $stateParams, GetBasePath) {
                            let path = `${GetBasePath('job_templates')}${$stateParams.id}/schedules`;
                            return qs.search(path, $stateParams[`${list.iterator}_search`]);
                        }
                    ],
                    ParentObject: ['$stateParams', 'Rest', 'GetBasePath', function($stateParams, Rest, GetBasePath){
                        let path = `${GetBasePath('job_templates')}${$stateParams.id}`;
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
                            list.basePath = GetBasePath('job_templates') + $stateParams.id + '/schedules/';
                            return list;
                        }
                    ]
                },
                views: {
                    '@': {
                        templateProvider: function(ScheduleList, generateList, ParentObject, $filter){
                            // include name of parent resource in listTitle
                            ScheduleList.listTitle = `${$filter('sanitize')(ParentObject.name)}<div class='List-titleLockup'></div>` + N_('SCHEDULES');
                            let html = generateList.build({
                                list: ScheduleList,
                                mode: 'edit'
                            });
                            html = generateList.wrapPanel(html);
                            return generateList.insertFormView() + html;
                        },
                        controller: 'schedulerListController'
                    }
                }
            });
            $stateExtender.addState({
                name: 'jobTemplateSchedules.add',
                route: '/add',
                views: {
                    'form': {
                        controller: 'schedulerAddController',
                        templateUrl: templateUrl("scheduler/schedulerForm"),
                    }
                },
                ncyBreadcrumb: {
                    parent: 'jobTemplateSchedules',
                    label: N_('CREATE SCHEDULE')
                }
            });
            $stateExtender.addState({
                name: 'jobTemplateSchedules.edit',
                route: '/:schedule_id',
                views: {
                    'form': {
                        controller: 'schedulerEditController',
                        templateUrl: templateUrl("scheduler/schedulerForm"),
                    }
                },
                ncyBreadcrumb: {
                    parent: 'jobTemplateSchedules',
                    label: '{{schedule_obj.name}}'
                }
            });

            // workflows
            $stateExtender.addState({
                searchPrefix: 'schedule',
                name: 'workflowJobTemplateSchedules',
                route: '/templates/workflow_job_template/:id/schedules',
                templateUrl: templateUrl("scheduler/scheduler"),
                controller: 'schedulerController',
                data: {
                    activityStream: true,
                    activityStreamTarget: 'job_template',
                    activityStreamId: 'id'
                },
                ncyBreadcrumb: {
                    parent: 'templates.editWorkflowJobTemplate({workflow_job_template_id: parentObject.id})',
                    label: N_('SCHEDULES')
                },
                resolve: {
                    Dataset: ['ScheduleList', 'QuerySet', '$stateParams', 'GetBasePath',
                        function(list, qs, $stateParams, GetBasePath) {
                            let path = `${GetBasePath('workflow_job_templates')}${$stateParams.id}/schedules`;
                            return qs.search(path, $stateParams[`${list.iterator}_search`]);
                        }
                    ],
                    ParentObject: ['$stateParams', 'Rest', 'GetBasePath', function($stateParams, Rest, GetBasePath){
                        let path = `${GetBasePath('workflow_job_templates')}${$stateParams.id}`;
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
                            list.basePath = GetBasePath('workflow_job_templates') + $stateParams.id + '/schedules/';
                            return list;
                        }
                    ]
                },
                views: {
                    '@': {
                        templateProvider: function(ScheduleList, generateList, ParentObject, $filter){
                            // include name of parent resource in listTitle
                            ScheduleList.listTitle = `${$filter('sanitize')(ParentObject.name)}<div class='List-titleLockup'></div>` + N_('SCHEDULES');
                            let html = generateList.build({
                                list: ScheduleList,
                                mode: 'edit'
                            });
                            html = generateList.wrapPanel(html);
                            return generateList.insertFormView() + html;
                        },
                        controller: 'schedulerListController'
                    }
                }
            });
            $stateExtender.addState({
                name: 'workflowJobTemplateSchedules.add',
                route: '/add',
                views: {
                    'form': {
                        controller: 'schedulerAddController',
                        templateUrl: templateUrl("scheduler/schedulerForm"),
                    }
                },
                ncyBreadcrumb: {
                    parent: 'workflowJobTemplateSchedules',
                    label: N_('CREATE SCHEDULE')
                }
            });
            $stateExtender.addState({
                name: 'workflowJobTemplateSchedules.edit',
                route: '/:schedule_id',
                views: {
                    'form': {
                        controller: 'schedulerEditController',
                        templateUrl: templateUrl("scheduler/schedulerForm"),
                    }
                },
                ncyBreadcrumb: {
                    parent: 'workflowJobTemplateSchedules',
                    label: '{{schedule_obj.name}}'
                }
            });
            // projects
            $stateExtender.addState({
                searchPrefix: 'schedule',
                name: 'projectSchedules',
                route: '/projects/:id/schedules',
                data: {
                    activityStream: true,
                    activityStreamTarget: 'project',
                    activityStreamId: 'id'
                },
                ncyBreadcrumb: {
                    parent: 'projects.edit({project_id: parentObject.id})',
                    label: N_('SCHEDULES')
                },
                resolve: {
                    Dataset: ['ScheduleList', 'QuerySet', '$stateParams', 'GetBasePath',
                        function(list, qs, $stateParams, GetBasePath) {
                            let path = `${GetBasePath('projects')}${$stateParams.id}/schedules`;
                            return qs.search(path, $stateParams[`${list.iterator}_search`]);
                        }
                    ],
                    ParentObject: ['$stateParams', 'Rest', 'GetBasePath', function($stateParams, Rest, GetBasePath){
                        let path = `${GetBasePath('projects')}${$stateParams.id}`;
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
                            list.basePath = GetBasePath('projects') + $stateParams.id + '/schedules/';
                            return list;
                        }
                    ]
                },
                views: {
                    '@': {
                        templateProvider: function(ScheduleList, generateList, ParentObject, $filter){
                            // include name of parent resource in listTitle
                            ScheduleList.listTitle = `${$filter('sanitize')(ParentObject.name)}<div class='List-titleLockup'></div>` + N_('SCHEDULES');
                            let html = generateList.build({
                                list: ScheduleList,
                                mode: 'edit'
                            });
                            html = generateList.wrapPanel(html);
                            return generateList.insertFormView() + html;
                        },
                        controller: 'schedulerListController'
                    }
                }
            });

            $stateExtender.addState({
                name: 'projectSchedules.add',
                route: '/add',
                ncyBreadcrumb: {
                    label: N_('CREATE SCHEDULE')
                },
                views: {
                    'form': {
                        controller: 'schedulerAddController',
                        templateUrl: templateUrl("scheduler/schedulerForm"),
                    }
                }
            });
            $stateExtender.addState({
                name: 'projectSchedules.edit',
                route: '/:schedule_id',
                ncyBreadcrumb: {
                    label: '{{schedule_obj.name}}'
                },
                views: {
                    'form': {
                        controller: 'schedulerEditController',
                        templateUrl: templateUrl("scheduler/schedulerForm"),
                    }
                }
            });
            // upcoming scheduled jobs
            $stateExtender.addState({
                searchPrefix: 'schedule',
                name: 'jobs.schedules',
                route: '/schedules',
                params: {
                    schedule_search: {
                        value: {
                            next_run__isnull: 'false',
                            order_by: 'unified_job_template__polymorphic_ctype__model'
                        },
                        dynamic: true
                    }
                },
                data: {
                    activityStream: false,
                },
                ncyBreadcrumb: {
                    parent: 'jobs',
                    label: N_('SCHEDULED')
                },
                resolve: {
                    ScheduleList: ['ScheduledJobsList', function(list){
                        return list;
                    }],
                    Dataset: ['ScheduleList', 'QuerySet', '$stateParams', 'GetBasePath',
                        function(list, qs, $stateParams, GetBasePath) {
                            let path = GetBasePath('schedules');
                            return qs.search(path, $stateParams[`${list.iterator}_search`]);
                        }
                    ],
                    ParentObject: ['GetBasePath', (GetBasePath) =>{return {endpoint:GetBasePath('schedules')}; }],
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
                        }]
                },
                views: {
                    'list@jobs': {
                        templateProvider: function(ScheduleList, generateList){
                            let html = generateList.build({
                                list: ScheduleList,
                                mode: 'edit',
                                title: false
                            });
                            return html;
                        },
                        controller: 'schedulerListController'
                    }
                }
            });
        }]);
