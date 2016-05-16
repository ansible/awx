/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

   /**
 * @ngdoc function
 * @name helpers.function:License
 * @description    Routines for checking and reporting license status
 *          CheckLicense.test() is called in app.js, in line 532, which is when the license is checked. The license information is
 *          stored in local storage using 'Store()'.
 *
 *
 *
 *
*/

// import '../forms';

export default
    ['$q', '$rootScope', '$compile', 'CreateDialog', 'Store',
    'GenerateForm', 'TextareaResize', 'ToJSON', 'GetBasePath',
    'Rest', 'ProcessErrors', 'Alert', 'IsAdmin', '$state', 'pendoService',
    'Authorization', 'Wait',
    function($q, $rootScope, $compile, CreateDialog, Store, GenerateForm,
        TextareaResize, ToJSON, GetBasePath, Rest, ProcessErrors, Alert, IsAdmin, $state,
        pendoService, Authorization, Wait) {
        return {
            getRemainingDays: function(time_remaining) {
                // assumes time_remaining will be in seconds
                var tr = parseInt(time_remaining, 10);
                return Math.floor(tr / 86400);
            },

            shouldNotify: function(license) {
                if (license && typeof license === 'object' && Object.keys(license).length > 0) {
                    // we have a license object
                    if (!license.valid_key) {
                        // missing valid key
                        return true;
                    }
                    else if (license.free_instances <= 0) {
                        // host count exceeded
                        return true;
                    }
                    else if (this.getRemainingDays(license.time_remaining) < 15) {
                        // below 15 days remaining on license
                        return true;
                    }
                    return false;
                } else {
                    // missing license object
                    return true;
                }
            },

            isAdmin: function() {
                return IsAdmin();
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
            postLicense: function(license_key, in_scope) {
                var url = GetBasePath('config'),
                    self = this,
                    json_data, scope;

                scope = (in_scope) ? in_scope : self.scope;

                json_data = ToJSON('json', license_key);
                json_data.eula_accepted = scope.eula_agreement;
                if (typeof json_data === 'object' && Object.keys(json_data).length > 0) {
                    Rest.setUrl(url);
                    Rest.post(json_data)
                        .success(function (response) {
                            response.license_info = response;
                            Alert('License Accepted', 'The Ansible Tower license was updated. To review or update the license, choose View License from the Setup menu.','alert-info');
                            $rootScope.features = undefined;

                            Authorization.getLicense()
                                .success(function (data) {
                                    Authorization.setLicense(data);
                                    pendoService.issuePendoIdentity();
                                    Wait("stop");
                                    $state.go('home');
                                })
                                .error(function () {
                                    Wait('stop');
                                    Alert('Error', 'Failed to access license information. GET returned status: ' + status, 'alert-danger',
                                        $state.go('signOut'));
                                });




                        })
                        .catch(function (response) {
                            scope.license_json_api_error = "A valid license key in JSON format is required";
                            ProcessErrors(scope, response.data, response.status, null, { hdr: 'Error!',
                                msg: 'Failed to update license. POST returned: ' + response.status
                            });
                        });
                } else {
                    scope.license_json_api_error = "A valid license key in JSON format is required";
                }
            },

            test: function() {
                var license = Store('license'),
                    self = this;
                    // scope;

                var getLicense = function() {
                    var deferred = $q.defer();

                    if (license === null) {
                        Rest.setUrl(GetBasePath('config'));
                        return Rest.get()
                            .then(function (data) {
                                license = data.data.license_info;
                                deferred.resolve();
                                return deferred.promise;
                            }, function () {
                                deferred.resolve();
                                return deferred.promise;
                            });
                    } else {
                        deferred.resolve(license);
                        return deferred.promise;
                    }
                };

                var promise = getLicense();
                promise.then(function() {
                    // self.scope = $rootScope.$new();
                    // scope = self.scope;

                    if (license && typeof license === 'object' && Object.keys(license).length > 0) {
                        // if (license.tested) {
                        //     return true;
                        // }
                        license.tested = true;
                        Store('license',license);  //update with tested flag
                    }

                    // Don't do anything when the license is valid
                    if (!self.shouldNotify(license)) {
                        $rootScope.licenseMissing = false;
                        return true; // if the license is valid it would exit 'test' here, otherwise it moves on to making the modal for the license
                    }
                    $rootScope.licenseMissing = true;
                    $state.go('license');
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
            GetLicense: function() {
                // Retrieve license detail
                var //self = this,
                    // scope = (inScope) ? inScope : self.scope,
                    url = GetBasePath('config');
                Rest.setUrl(url);
                return Rest.get()
                .success(function(res){
                    $rootScope.license_tested = true;
                    return res;
                })
                .error(function (data, status) {
                    ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to retrieve license. GET status: ' + status
                    });
                });
            }
        };
    }];
