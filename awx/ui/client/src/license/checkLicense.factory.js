/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
	['$state', '$rootScope', 'Rest', 'GetBasePath', 'ProcessErrors', '$q',
		'ConfigService',
	function($state, $rootScope, Rest, GetBasePath, ProcessErrors, $q,
		ConfigService){
			return {
				get: function() {
					var config = ConfigService.get();
					return config.license_info;
				},

				post: function(license, eula){
					var defaultUrl = GetBasePath('config');
					Rest.setUrl(defaultUrl);
					var data = license;
					data.eula_accepted = eula;
					return Rest.post(JSON.stringify(data))
						.success(function(res){
							return res;
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
					 		return false;
					 	}
					 	else if (license.free_instances <= 0){
					 		return false;
					 	}
					 	// notify if less than 15 days remaining
					 	else if (license.time_remaining / 1000 / 60 / 60 / 24 > 15){
					 		return false;
					 	}
					 	return true;
				},
				test: function(event){
					var deferred = $q.defer(),
						license = this.get();
					if(license === null || !$rootScope.license_tested){
						if(this.valid(license) === false) {
							$rootScope.licenseMissing = true;
							if(event){
								event.preventDefault();
							}
							$state.go('license');
							deferred.reject();
						}
						else {
							$rootScope.licenseMissing = false;
							deferred.resolve();
						}
					}
					else if(this.valid(license) === false) {
						$rootScope.licenseMissing = true;
						$state.transitionTo('license');
						if(event){
							event.preventDefault();
						}
						deferred.reject(license);
					}
					else {
						$rootScope.licenseMissing = false;
						deferred.resolve(license);
					}
					return deferred.promise;
				}

			};
		}
		];
