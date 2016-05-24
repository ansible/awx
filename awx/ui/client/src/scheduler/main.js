/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import controller from './scheduler.controller';
import addController from './schedulerAdd.controller';
import editController from './schedulerEdit.controller';
import {templateUrl} from '../shared/template-url/template-url.factory';

export default
    angular.module('scheduler', [])
        .controller('schedulerController', controller)
        .controller('schedulerAddController', addController)
        .controller('schedulerEditController', editController)
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState({
                name: 'jobTemplateSchedules',
                route: '/job_templates/:id/schedules',
                templateUrl: templateUrl("scheduler/scheduler"),
                controller: 'schedulerController'
            });
            $stateExtender.addState({
                name: 'jobTemplateSchedules.add',
                route: '/add',
                templateUrl: templateUrl("scheduler/schedulerForm"),
                controller: 'schedulerAddController'
            });
            $stateExtender.addState({
                name: 'jobTemplateSchedules.edit',
                route: '/:schedule_id',
                templateUrl: templateUrl("scheduler/schedulerForm"),
                controller: 'schedulerEditController'
            });
            $stateExtender.addState({
                name: 'projectSchedules',
                route: '/projects/:id/schedules',
                templateUrl: templateUrl("scheduler/scheduler"),
                controller: 'schedulerController'
            });
            $stateExtender.addState({
                name: 'projectSchedules.add',
                route: '/add',
                templateUrl: templateUrl("scheduler/schedulerForm"),
                controller: 'schedulerAddController'
            });
            $stateExtender.addState({
                name: 'projectSchedules.edit',
                route: '/:schedule_id',
                templateUrl: templateUrl("scheduler/schedulerForm"),
                controller: 'schedulerEditController'
            });
            $stateExtender.addState({
                name: 'inventoryManage.schedules',
                route: '/schedules/:id',
                views: {
                    'form@inventoryManage': {
                        templateUrl: templateUrl("scheduler/scheduler"),
                        controller: 'schedulerController'
                    }
                },
                ncyBreadcrumb: {
                    label: "{{name}} SCHEDULES"
                },
            });
            $stateExtender.addState({
                name: 'inventoryManage.schedules.add',
                route: '/add',
                templateUrl: templateUrl("scheduler/schedulerForm"),
                controller: 'schedulerAddController'
            });
            $stateExtender.addState({
                name: 'inventoryManage.schedules.edit',
                route: '/:schedule_id',
                templateUrl: templateUrl("scheduler/schedulerForm"),
                controller: 'schedulerEditController'
            });
        }]);
