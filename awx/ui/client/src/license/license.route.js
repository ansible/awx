/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../shared/template-url/template-url.factory';
import { N_ } from '../i18n';
import _ from 'lodash';

export default {
	name: 'license',
	route: '/license',
	templateUrl: templateUrl('license/license'),
	controller: 'licenseController',
	data: {},
	ncyBreadcrumb: {
		label: N_('LICENSE')
	},
	onEnter: ['$state', 'ConfigService', (state, configService) => {
		return configService.getConfig()
			.then(config => {
				if (_.get(config, 'license_info.license_type') === 'open') {
					return state.go('setup');
				}
			});
	}],
	resolve: {
		features: ['CheckLicense', '$rootScope',
			function(CheckLicense, $rootScope) {
				if($rootScope.licenseMissing === undefined){
					return CheckLicense.notify();
				}
			}
		],
		config: ['ConfigService', 'CheckLicense', '$rootScope',
			function(ConfigService, CheckLicense, $rootScope) {
				ConfigService.delete();
				return ConfigService.getConfig()
				.then(function(config){
					$rootScope.licenseMissing = (CheckLicense.valid(config.license_info) === false) ? true : false;
					return config;
				});
			}
		],
		rhCreds: ['Rest', 'GetBasePath', function(Rest, GetBasePath) {
			Rest.setUrl(`${GetBasePath('settings')}system/`);
			return Rest.get()
					.then(({data}) => {
						const rhCreds = {};
						if (data.REDHAT_USERNAME && data.REDHAT_USERNAME !== "") {
								rhCreds.REDHAT_USERNAME = data.REDHAT_USERNAME;
						}

						if (data.REDHAT_PASSWORD && data.REDHAT_PASSWORD !== "") {
								rhCreds.REDHAT_PASSWORD = data.REDHAT_PASSWORD;
						}
						
						return rhCreds;
					}).catch(() => {
							return {};
					});
		}]
	},
};
