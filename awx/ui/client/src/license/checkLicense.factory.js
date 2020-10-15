/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
	['$state', '$rootScope', 'Rest', 'GetBasePath',
		'ConfigService', '$q',
	function($state, $rootScope, Rest, GetBasePath,
		ConfigService, $q){
			return {
				get: function() {
					var config = ConfigService.get();
					return config.license_info;
				},

				post: function(payload, eula, attach){
					var defaultUrl = GetBasePath('config') + (attach ? 'attach/' : '');
					Rest.setUrl(defaultUrl);
					var data = payload;
					
					if (!attach) {
						data.eula_accepted = eula;
					}

					return Rest.post(JSON.stringify(data))
						.then((response) =>{
							if (attach) {
								var configPayload = {};
								configPayload.eula_accepted = eula;
								Rest.setUrl(GetBasePath('config'));
								return Rest.post(configPayload)
									.then((configResponse) => {
										return configResponse.data;
									});
							}
							return response.data;
						})
						.catch(({data}) => {
							return $q.reject(data);
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
