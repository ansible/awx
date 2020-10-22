/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {N_} from "../i18n";

export default
    ['Wait', '$state', '$scope', '$rootScope', 'ProcessErrors', 'CheckLicense', 'moment', '$timeout', 'Rest', 'LicenseStrings',
    '$window', 'ConfigService', 'pendoService', 'insightsEnablementService', 'i18n', 'config', 'subscriptionCreds', 'GetBasePath',
    function(Wait, $state, $scope, $rootScope, ProcessErrors, CheckLicense, moment, $timeout, Rest, LicenseStrings,
    $window, ConfigService, pendoService, insightsEnablementService, i18n, config, subscriptionCreds, GetBasePath) {

        $scope.strings = LicenseStrings;

        const calcDaysRemaining = function(seconds) {
      	 		// calculate the number of days remaining on the license
      			let duration = moment.duration(seconds, 'seconds').asDays();

      			duration = Math.floor(duration);
                if(duration < 0){
                    duration = 0;
                }

                duration = (duration!==1) ? `${duration} Days` : `${duration} Day`;

    			      return duration;
    	 	};

        const calcExpiresOn = function(seconds) {
            // calculate the expiration date of the license
            return moment.unix(seconds).calendar();
        };

        const reset = function() {
            $scope.newLicense.eula = undefined;
            $scope.subscriptionCreds = {};
            $scope.selectedLicense = {};
        };

        const initVars = (config) => {
            // license/license.partial.html compares fileName
            $scope.fileName = N_("No file selected.");

            if ($rootScope.licenseMissing) {
                $scope.title = $rootScope.BRAND_NAME + i18n._(" Subscription");
            } else {
                $scope.title = i18n._("Subscription Management");
            }

            $scope.license = config;
            $scope.license.version = config.version.split('-')[0];
            $scope.time = {};
            $scope.time.remaining = calcDaysRemaining($scope.license.license_info.time_remaining);
            $scope.time.expiresOn = calcExpiresOn($scope.license.license_info.license_date);
            $scope.valid = CheckLicense.valid($scope.license.license_info);
            $scope.compliant = $scope.license.license_info.compliant;
            $scope.selectedLicense = {};
            $scope.newLicense = {
                pendo: true,
                insights: true
            };

            $scope.subscriptionCreds = {};

            if (subscriptionCreds.SUBSCRIPTIONS_USERNAME && subscriptionCreds.SUBSCRIPTIONS_USERNAME !== "") {
                $scope.subscriptionCreds.username = subscriptionCreds.SUBSCRIPTIONS_USERNAME;
            }

            if (subscriptionCreds.SUBSCRIPTIONS_PASSWORD && subscriptionCreds.SUBSCRIPTIONS_PASSWORD !== "") {
                $scope.subscriptionCreds.password = subscriptionCreds.SUBSCRIPTIONS_PASSWORD;
                $scope.showPlaceholderPassword = true;
            }
        };

        const updateSubscriptionCreds = (config) => {
            Rest.setUrl(`${GetBasePath('settings')}system/`);
            Rest.get()
                .then(({data}) => {
                    initVars(config);

                    if (data.SUBSCRIPTIONS_USERNAME && data.SUBSCRIPTIONS_USERNAME !== "") {
                        $scope.subscriptionCreds.username = data.SUBSCRIPTIONS_USERNAME;
                    }

                    if (data.SUBSCRIPTIONS_PASSWORD && data.SUBSCRIPTIONS_PASSWORD !== "") {
                        $scope.subscriptionCreds.password = data.SUBSCRIPTIONS_PASSWORD;
                        $scope.showPlaceholderPassword = true;
                    }
                }).catch(() => {
                    initVars(config);
                });
        };
        
        initVars(config);

        $scope.getKey = function(event) {
            // Mimic HTML5 spec, show filename
            $scope.fileName = event.target.files[0].name;
            // Grab the key from the raw license file
            const raw = new FileReader();

            raw.onload = function() {
                $scope.newLicense.manifest = btoa(raw.result);
            };

            try {
                raw.readAsBinaryString(event.target.files[0]);
            } catch(err) {
                ProcessErrors($rootScope, null, null, null,
                    {msg: i18n._('Invalid file format. Please upload a valid Red Hat Subscription Manifest.')});
            }
        };

        // HTML5 spec doesn't provide a way to customize file input css
        // So we hide the default input, show our own, and simulate clicks to the hidden input
        $scope.fakeClick = function() {
            if($scope.user_is_superuser && (!$scope.subscriptionCreds.username || $scope.subscriptionCreds.username === '') && (!$scope.subscriptionCreds.password || $scope.subscriptionCreds.password === '')) {
                $('#License-file').click();
            }
        };

        $scope.downloadLicense = function() {
            $window.open('https://www.ansible.com/license', '_blank');
        };

        $scope.replacePassword = () => {
            if ($scope.user_is_superuser && !$scope.newLicense.manifest) {
                $scope.showPlaceholderPassword = false;
                $scope.subscriptionCreds.password = "";
                $timeout(() => {
                    $('.tooltip').remove();
                    $('#rh-password').focus();
                });
            }
        };

        $scope.lookupLicenses = () => {
            if ($scope.subscriptionCreds.username && $scope.subscriptionCreds.password) {
                Wait('start');
                ConfigService.getSubscriptions($scope.subscriptionCreds.username, $scope.subscriptionCreds.password)
                    .then(({data}) => {
                        Wait('stop');
                        if (data && data.length > 0) {
                            $scope.rhLicenses = data;
                            if ($scope.selectedLicense.fullLicense) {
                                $scope.selectedLicense.modalKey = $scope.selectedLicense.fullLicense.license_key;
                            }
                            $scope.showLicenseModal = true;
                        } else {
                            ProcessErrors($scope, data, status, null, {
                                hdr: i18n._('No Licenses Found'),
                                msg: i18n._('We were unable to locate licenses associated with this account')
                            });
                        }
                    })
                    .catch(({data, status}) => {
                        Wait('stop');
                        ProcessErrors($scope, data, status, null, {
                            hdr: i18n._('Error Fetching Licenses')
                        });
                    });
            }
        };

        $scope.confirmLicenseSelection = () => {
            $scope.showLicenseModal = false;
            $scope.selectedLicense.fullLicense = $scope.rhLicenses.find((license) => {
                return license.pool_id === $scope.selectedLicense.modalPoolId;
            });
            $scope.selectedLicense.modalPoolId = undefined;
        };

        $scope.cancelLicenseLookup = () => {
            $scope.showLicenseModal = false;
            $scope.selectedLicense.modalPoolId = undefined;
        };

        $scope.submit = function() {
            Wait('start');
            let payload = {};
            let attach = false;
            if ($scope.newLicense.manifest) {
                payload.manifest = $scope.newLicense.manifest;
            } else if ($scope.selectedLicense.fullLicense) {
                payload.pool_id = $scope.selectedLicense.fullLicense.pool_id;
                attach = true;
            }
            
            CheckLicense.post(payload, $scope.newLicense.eula, attach)
                .finally((licenseInfo) => {
                    reset();
                    ConfigService.delete();
                    ConfigService.getConfig(licenseInfo)
                        .then(function(config) {

                            if ($rootScope.licenseMissing === true) {
                                if ($scope.newLicense.pendo) {
                                    pendoService.updatePendoTrackingState('detailed');
                                    pendoService.issuePendoIdentity();
                                } else {
                                    pendoService.updatePendoTrackingState('off');
                                }

                                if ($scope.newLicense.insights) {
                                    insightsEnablementService.updateInsightsTrackingState(true);
                                } else {
                                    insightsEnablementService.updateInsightsTrackingState(false);
                                }

                                $state.go('dashboard', {
                                        licenseMissing: false
                                });
                            } else {
                                updateSubscriptionCreds(config);
                                $scope.success = true;
                                $rootScope.licenseMissing = false;
                                // for animation purposes
                                const successTimeout = setTimeout(function() {
                                        $scope.success = false;
                                        clearTimeout(successTimeout);
                                }, 4000);
                            }
                        });
                }).catch((err) => {
                    ProcessErrors($scope, err, null, null, {
                        hdr: i18n._('Error Applying License')
                    });
                });
        };
}];
