/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import controller from './scheduler.controller';
import addController from './schedulerAdd.controller';
import editController from './schedulerEdit.controller';
import {templateUrl} from '../shared/template-url/template-url.factory';
import schedulerDatePicker from './schedulerDatePicker.directive';

export default
    angular.module('scheduler', [])
        .controller('schedulerController', controller)
        .controller('schedulerAddController', addController)
        .controller('schedulerEditController', editController)
        .directive('schedulerDatePicker', schedulerDatePicker)
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState({
                name: 'jobTemplateSchedules',
                route: '/job_templates/:id/schedules',
                templateUrl: templateUrl("scheduler/scheduler"),
                controller: 'schedulerController',
                ncyBreadcrumb: {
                    parent: 'jobTemplates.edit',
                    label: 'SCHEDULES'
                }
            });
            $stateExtender.addState({
                name: 'jobTemplateSchedules.add',
                route: '/add',
                templateUrl: templateUrl("scheduler/schedulerForm"),
                controller: 'schedulerAddController',
                ncyBreadcrumb: {
                    parent: 'jobTemplateSchedules',
                    label: 'CREATE SCHEDULE'
                }
            });
            $stateExtender.addState({
                name: 'jobTemplateSchedules.edit',
                route: '/:schedule_id',
                templateUrl: templateUrl("scheduler/schedulerForm"),
                controller: 'schedulerEditController',
                ncyBreadcrumb: {
                    parent: 'jobTemplateSchedules',
                    label: '{{schedule_obj.name}}'
                }
            });
            $stateExtender.addState({
                name: 'projectSchedules',
                route: '/projects/:id/schedules',
                templateUrl: templateUrl("scheduler/scheduler"),
                controller: 'schedulerController',
                ncyBreadcrumb: {
                    parent: 'projects.edit',
                    label: 'SCHEDULES'
                }
            });
            $stateExtender.addState({
                name: 'projectSchedules.add',
                route: '/add',
                templateUrl: templateUrl("scheduler/schedulerForm"),
                controller: 'schedulerAddController',
                ncyBreadcrumb: {
                    parent: 'projectSchedules',
                    label: 'CREATE SCHEDULE'
                }
            });
            $stateExtender.addState({
                name: 'projectSchedules.edit',
                route: '/:schedule_id',
                templateUrl: templateUrl("scheduler/schedulerForm"),
                controller: 'schedulerEditController',
                ncyBreadcrumb: {
                    parent: 'projectSchedules',
                    label: '{{schedule_obj.name}}'
                }
            });
            $stateExtender.addState({
                name: 'inventoryManage.schedules',
                route: '/:id/schedules',
                views: {
                    'form@inventoryManage': {
                        templateUrl: templateUrl("scheduler/scheduler"),
                        controller: 'schedulerController'
                    }
                },
                ncyBreadcrumb: {
                    label: "SCHEDULES"
                }
            });
            $stateExtender.addState({
                name: 'inventoryManage.schedules.add',
                route: '/add',
                templateUrl: templateUrl("scheduler/schedulerForm"),
                controller: 'schedulerAddController',
                ncyBreadcrumb: {
                    label: "CREATE SCHEDULE"
                }
            });
            $stateExtender.addState({
                name: 'inventoryManage.schedules.edit',
                route: '/:schedule_id',
                templateUrl: templateUrl("scheduler/schedulerForm"),
                controller: 'schedulerEditController',
                ncyBreadcrumb: {
                    label: "{{schedule_obj.name}}"
                }
            });
        }]);
