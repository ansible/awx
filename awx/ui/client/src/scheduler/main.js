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
                controller: 'schedulerController',
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            });
            $stateExtender.addState({
                name: 'jobTemplateSchedules.add',
                route: '/add',
                templateUrl: templateUrl("scheduler/schedulerForm"),
                controller: 'schedulerAddController',
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }],
                    JobTemplateExtraVars: ['Rest', 'GetBasePath', 'ToJSON', '$stateParams', function(Rest, GetBasePath, ToJSON, $stateParams) {
                        var defaultUrl = GetBasePath('job_templates') + $stateParams.id + '/';
                        Rest.setUrl(defaultUrl);
                        return Rest.get().then(function(res){ 
                            // handle unescaped newlines
                            return JSON.parse(JSON.stringify(res.data.extra_vars));
                        });
                     }]
                }
            });
            $stateExtender.addState({
                name: 'jobTemplateSchedules.edit',
                route: '/:schedule_id',
                templateUrl: templateUrl("scheduler/schedulerForm"),
                controller: 'schedulerEditController',
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            });
            $stateExtender.addState({
                name: 'projectSchedules',
                route: '/projects/:id/schedules',
                templateUrl: templateUrl("scheduler/scheduler"),
                controller: 'schedulerController',
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }],
                    JobTemplateExtraVars: function(){
                        return null;
                    }
                }
            });
            $stateExtender.addState({
                name: 'projectSchedules.add',
                route: '/add',
                templateUrl: templateUrl("scheduler/schedulerForm"),
                controller: 'schedulerAddController',
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }],
                        JobTemplateExtraVars: function(){
                        return null;
                    }
                }
            });
            $stateExtender.addState({
                name: 'projectSchedules.edit',
                route: '/:schedule_id',
                templateUrl: templateUrl("scheduler/schedulerForm"),
                controller: 'schedulerEditController',
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            });
        }]);
