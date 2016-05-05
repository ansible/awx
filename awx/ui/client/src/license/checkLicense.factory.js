/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
	['$state', '$rootScope', 'Rest', 'GetBasePath', 'ProcessErrors', '$q',
	function($state, $rootScope, Rest, GetBasePath, ProcessErrors, $q){
			return {
				get: function() {
					var defaultUrl = GetBasePath('config');
					Rest.setUrl(defaultUrl);
					return Rest.get()
						.success(function(res){
							$rootScope.license_tested = true;
							return res;
						})
	                    .error(function(res, status){
	                        ProcessErrors($rootScope, res, status, null, {hdr: 'Error!',
	                        msg: 'Call to '+ defaultUrl + ' failed. Return status: '+ status});
	                    });
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
				notify: function(){
					var deferred = $q.defer(),
						self = this;
					if($rootScope.license_tested !== true){
						this.get()
							.then(function(res){
								if(self.valid(res.data.license_info) === false) {
									$rootScope.licenseMissing = true;
									deferred.resolve();
									$state.go('license');
								}
								else {
									$rootScope.licenseMissing = false;
								}
							});
					}
					else{
						deferred.resolve();
					}

					return deferred.promise;
				}

			};
		}
		];
