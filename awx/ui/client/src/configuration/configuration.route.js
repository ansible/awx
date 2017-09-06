/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import {templateUrl} from '../shared/template-url/template-url.factory';
 import ConfigurationController from './configuration.controller';
 import { N_ } from '../i18n';

// Import form controllers
 import ConfigurationAuthController from './auth-form/configuration-auth.controller';
 import ConfigurationJobsController from './jobs-form/configuration-jobs.controller';
 import ConfigurationSystemController from './system-form/configuration-system.controller';
 import ConfigurationUiController from './ui-form/configuration-ui.controller';

 export default {
     name: 'configuration',
     route: '/configuration/:currentTab',
     params: {
         currentTab: {
             value: 'auth',
             dynamic: true,
             isOptional: true
         }

     },
     ncyBreadcrumb: {
         label: N_("EDIT CONFIGURATION")
     },
     controller: ConfigurationController,
     resolve: {
         configDataResolve: ['ConfigurationService', function(ConfigurationService){
             return ConfigurationService.getConfigurationOptions();
         }]
     },
     views: {
         '': {
             templateUrl: templateUrl('configuration/configuration'),
             controller: ConfigurationController,
             controllerAs: 'vm'
         },
         'auth@configuration': {
             templateUrl: templateUrl('configuration/auth-form/configuration-auth'),
             controller: ConfigurationAuthController,
             controllerAs: 'authVm'
         },
         'jobs@configuration': {
             templateUrl: templateUrl('configuration/jobs-form/configuration-jobs'),
             controller: ConfigurationJobsController,
             controllerAs: 'jobsVm'
         },
         'system@configuration': {
             templateUrl: templateUrl('configuration/system-form/configuration-system'),
             controller: ConfigurationSystemController,
             controllerAs: 'systemVm'
         },
         'ui@configuration': {
             templateUrl: templateUrl('configuration/ui-form/configuration-ui'),
             controller: ConfigurationUiController,
             controllerAs: 'uiVm'
         }
     },
 };
