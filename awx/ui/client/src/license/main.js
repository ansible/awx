/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './license.route';
import controller from './license.controller';

export default
	angular.module('license', [])
		.controller('licenseController', controller)
		.factory('CheckLicense', ['$state', '$rootScope', 'Rest', 'GetBasePath', 'ProcessErrors', function($state, $rootScope, Rest, GetBasePath, ProcessErrors){
			return {
				get: function() {
					var defaultUrl = GetBasePath('config');
					Rest.setUrl(defaultUrl);
					return Rest.get()
						.success(function(res){
							return res
						})
	                    .error(function(res, status){
	                        ProcessErrors($rootScope, res, status, null, {hdr: 'Error!',
	                        msg: 'Call to '+ defaultUrl + ' failed. Return status: '+ status});
	                    });
				},
				post: function(license, eula){
					var defaultUrl = GetBasePath('config');
					Rest.setUrl(defaultUrl);
					var data = {
						eula_accepted: eula,
						license_key: license
					};
					console.log(data)
					return Rest.post(JSON.stringify(data))
						.success(function(res){
							return res
						})
						.error(function(res, status){
	                        ProcessErrors($rootScope, res, status, null, {hdr: 'Error!',
	                        msg: 'Call to '+ defaultUrl + ' failed. Return status: '+ status});
	                    });
				},
				// Checks current license validity
				// Intended to for runtime or pre-state checks
				// Returns false if invalid
				valid: function(license) {
					 	if (!license.valid_key){
					 		return false
					 	}
					 	else if (license.free_instances <= 0){
					 		return false
					 	}
					 	// notify if less than 15 days remaining 
					 	else if (license.time_remaining / 1000 / 60 / 60 / 24 > 15){
					 		return false
					 	}
					 	return true
				},
				notify: function(){
					this.get()
						.then(function(res){
							this.valid(res.license_info) ? null : $state.go('license');
						});
				}

			}
		}])
		.run(['$stateExtender', function($stateExtender) {
			$stateExtender.addState(route);
		}]);