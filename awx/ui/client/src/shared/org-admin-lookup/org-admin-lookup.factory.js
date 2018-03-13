/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
	['Rest', 'Authorization', 'GetBasePath', 'ProcessErrors', '$rootScope', '$q',
	function(Rest, Authorization, GetBasePath, ProcessErrors, $rootScope, $q){
			return {
				checkForAdminAccess: function(params) {
                    // params.organization - id of the organization in question
                    var deferred = $q.defer();
                    if(Authorization.getUserInfo('is_superuser') !== true) {
                        Rest.setUrl(GetBasePath('users') + $rootScope.current_user.id + '/admin_of_organizations');
                        Rest.get({ params: { id: params.organization } })
                            .then(({data}) => {
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
                },

				checkForRoleLevelAdminAccess: function(organization_id, role_level) {
                    let deferred = $q.defer();
                    let params = {
                        role_level,
                        id: organization_id
                    };

                    if(Authorization.getUserInfo('is_superuser') !== true) {
                        Rest.setUrl(GetBasePath('organizations'));
                        Rest.get({ params: params })
                            .then(({data}) => {
                                if(data.count && data.count > 0) {
                                    deferred.resolve(true);
                                }
                                else {
                                    deferred.resolve(false);
                                }
                            })
                            .catch(({data, status}) => {
                                ProcessErrors(null, data, status, null, {
                                    hdr: 'Error!',
                                    msg: 'Failed to get organization data based on role_level. Return status: ' + status
                                });
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
