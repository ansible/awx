/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
	['Rest', 'Authorization', 'GetBasePath', '$rootScope', '$q',
	function(Rest, Authorization, GetBasePath, $rootScope, $q){
			return {
				checkForAdminAccess: function(params) {
                    // params.organization - id of the organization in question
                    var deferred = $q.defer();
                    if(Authorization.getUserInfo('is_superuser') !== true) {
                        Rest.setUrl(GetBasePath('users') + $rootScope.current_user.id + '/admin_of_organizations');
                        Rest.get({ params: { id: params.organization } })
                            .success(function(data) {
                                if(data.count && data.count > 0) {
                                    deferred.resolve(true);
                                }
                                else {
                                    deferred.resolve(false);
                                }
                            });
                    }
                    else {
                        deferred.resolve(true);
                    }

                    return deferred.promise;
				}

			};
		}
	];
