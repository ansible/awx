/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


import {templateUrl} from '../../shared/template-url/template-url.factory';
import controller from '../../scheduler/scheduler.controller';
import addController from '../../scheduler/schedulerAdd.controller';
import editController from '../../scheduler/schedulerEdit.controller';

export default
    angular.module('managementJobScheduler', [])
        .controller('managementJobController', controller)
        .controller('managementJobAddController', addController)
        .controller('managementJobEditController', editController)
        .run(['$stateExtender', function($stateExtender){
            $stateExtender.addState({
                name: 'managementJobSchedules',
                route: '/management_jobs/:id/schedules',
                templateUrl: templateUrl('scheduler/scheduler'),
                controller: 'managementJobController',
                resolve: {
                    features: ['FeaturesService', function(FeaturesService){
                        return FeaturesService.get();
                    }]
                }
            });
            $stateExtender.addState({
                name: 'managementJobSchedules.add',
                route: '/add',
                templateUrl: templateUrl('management-jobs/scheduler/schedulerForm'),
                controller: 'managementJobAddController',
                resolve: {
                    features: ['FeaturesService', function(FeaturesService){
                        return FeaturesService.get();
                    }]
                } 
            });
            $stateExtender.addState({
                name: 'managementJobSchedules.edit',
                route: '/add',
                templateUrl: templateUrl('management-jobs/scheduler/schedulerForm'),
                controller: 'managementJobEditController',
                resolve: {
                    features: ['FeaturesService', function(FeaturesService){
                        return FeaturesService.get();
                    }]
                } 
            });
        }]);