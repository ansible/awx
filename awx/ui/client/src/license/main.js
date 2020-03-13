/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './license.route';
import controller from './license.controller';
import CheckLicense from './checkLicense.factory';
import fileOnChange from './fileOnChange.directive';
import LicenseStrings from './license.strings';

export default
	angular.module('license', [])
		.controller('licenseController', controller)
		.directive('fileOnChange', fileOnChange)
		.factory('CheckLicense', CheckLicense)
		.service('LicenseStrings', LicenseStrings)
		.run(['$stateExtender', function($stateExtender) {
			$stateExtender.addState(route);
		}]);
