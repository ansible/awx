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

export default
    angular.module('scheduler', [])
        .controller('schedulerListController', listController)
        .controller('schedulerAddController', addController)
        .controller('schedulerEditController', editController)
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
                    label: 'SCHEDULES'
                },
                resolve: {
                    Dataset: ['SchedulesList', 'QuerySet', '$stateParams', 'GetBasePath',
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
                        }]
                },
                views: {
                    '@': {
                        templateProvider: function(SchedulesList, generateList, ParentObject){
                            // include name of parent resource in listTitle
                            SchedulesList.listTitle = `${ParentObject.name}<div class='List-titleLockup'></div>Schedules`;
                            let html = generateList.build({
                                list: SchedulesList,
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
                    label: 'CREATE SCHEDULE'
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
                    label: 'SCHEDULES'
                },
                resolve: {
                    Dataset: ['SchedulesList', 'QuerySet', '$stateParams', 'GetBasePath',
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
                        }]
                },
                views: {
                    '@': {
                        templateProvider: function(SchedulesList, generateList, ParentObject){
                            // include name of parent resource in listTitle
                            SchedulesList.listTitle = `${ParentObject.name}<div class='List-titleLockup'></div>Schedules`;
                            let html = generateList.build({
                                list: SchedulesList,
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
                    label: 'CREATE SCHEDULE'
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
                    label: 'SCHEDULES'
                },
                resolve: {
                    Dataset: ['SchedulesList', 'QuerySet', '$stateParams', 'GetBasePath',
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
                        }]
                },
                views: {
                    '@': {
                        templateProvider: function(SchedulesList, generateList, ParentObject){
                            // include name of parent resource in listTitle
                            SchedulesList.listTitle = `${ParentObject.name}<div class='List-titleLockup'></div>Schedules`;
                            let html = generateList.build({
                                list: SchedulesList,
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
                    label: 'CREATE SCHEDULE'
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
                        }
                    }
                },
                data: {
                    activityStream: true,
                    activityStreamTarget: 'job',
                    activityStreamId: 'id'
                },
                ncyBreadcrumb: {
                    parent: 'jobs',
                    label: 'SCHEDULED'
                },
                resolve: {
                    SchedulesList: ['ScheduledJobsList', function(list){
                        return list;
                    }],
                    Dataset: ['SchedulesList', 'QuerySet', '$stateParams', 'GetBasePath',
                        function(list, qs, $stateParams, GetBasePath) {
                            let path = GetBasePath('schedules');
                            return qs.search(path, $stateParams[`${list.iterator}_search`]);
                        }
                    ],
                    ParentObject: [() =>{return {endpoint:'/api/v1/schedules'}; }],
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
                        templateProvider: function(SchedulesList, generateList){
                            let html = generateList.build({
                                list: SchedulesList,
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
