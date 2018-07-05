import { N_ } from '../i18n';
import {templateUrl} from '../shared/template-url/template-url.factory';
import SettingsController from './settings.controller';
// Import form controllers

export default {
    name: 'settings',
    route: '/settings',
    ncyBreadcrumb: {
        label: N_("SETTINGS")
    },
    resolve: {
        configDataResolve: ['SettingsService', function(SettingsService){
            return SettingsService.getConfigurationOptions();
        }],
        features: ['CheckLicense', '$rootScope',
			function(CheckLicense, $rootScope) {
				if($rootScope.licenseMissing === undefined){
					return CheckLicense.notify();
				}

		}],
		config: ['ConfigService', 'CheckLicense', '$rootScope',
			function(ConfigService, CheckLicense, $rootScope) {
				ConfigService.delete();
	            return ConfigService.getConfig()
					.then(function(config){
						$rootScope.licenseMissing = (CheckLicense.valid(config.license_info) === false) ? true : false;
						return config;
					});
			}],
    },
    views: {
        '': {
            templateUrl: templateUrl('configuration/settings'),
            controller: SettingsController,
            controllerAs: 'vm'
        }
    }
};