/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
	['$state', '$rootScope', 'Rest', 'GetBasePath', 'ProcessErrors',
		'ConfigService',
	function($state, $rootScope, Rest, GetBasePath, ProcessErrors,
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
						.then((response) =>{
							return response.data;
						})
						.catch(({res, status}) => {
	                        ProcessErrors($rootScope, res, status, null, {hdr: 'Error!',
	                        msg: 'Call to '+ defaultUrl + ' failed. Return status: '+ status});
	                    });
				},

				valid: function(license) {
					if (!license.valid_key){
						return false;
					}
					return true;
				},

				test: function(event){
					var license = this.get();
					if(license === null || !$rootScope.license_tested){
						if(this.valid(license) === false) {
							$rootScope.licenseMissing = true;
							$state.go('license');
							if(event){
								event.preventDefault();
							}
						}
						else {
							$rootScope.licenseMissing = false;
						}
					}
					else if(this.valid(license) === false) {
						$rootScope.licenseMissing = true;
						$state.go('license');
						if(event){
							event.preventDefault();
						}
					}
					else {
						$rootScope.licenseMissing = false;
					}
					return;
				}

			};
		}
		];
