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
		label: N_('SUBSCRIPTION')
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
		subscriptionCreds: ['Rest', 'GetBasePath', function(Rest, GetBasePath) {
			Rest.setUrl(`${GetBasePath('settings')}system/`);
			return Rest.get()
					.then(({data}) => {
						const subscriptionCreds = {};
						if (data.SUBSCRIPTIONS_USERNAME && data.SUBSCRIPTIONS_USERNAME !== "") {
								subscriptionCreds.SUBSCRIPTIONS_USERNAME = data.SUBSCRIPTIONS_USERNAME;
						}

						if (data.SUBSCRIPTIONS_PASSWORD && data.SUBSCRIPTIONS_PASSWORD !== "") {
								subscriptionCreds.SUBSCRIPTIONS_PASSWORD = data.SUBSCRIPTIONS_PASSWORD;
						}

						return subscriptionCreds;
					}).catch(() => {
							return {};
					});
		}]
	},
};
