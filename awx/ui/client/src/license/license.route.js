/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../shared/template-url/template-url.factory';
import { N_ } from '../i18n';

export default {
	name: 'license',
	route: '/license',
	templateUrl: templateUrl('license/license'),
	controller: 'licenseController',
	data: {},
	ncyBreadcrumb: {
		parent: 'setup',
		label: N_('LICENSE')
	},
	resolve: {
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
			}]
	},
};
