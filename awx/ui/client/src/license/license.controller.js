/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {N_} from "../i18n";

export default
    ['Wait', '$state', '$scope', '$rootScope', 'ProcessErrors', 'CheckLicense', 'moment', '$timeout', 'Rest', 'LicenseStrings',
    '$window', 'ConfigService', 'pendoService', 'insightsEnablementService', 'i18n', 'config', 'rhCreds', 'GetBasePath',
    function(Wait, $state, $scope, $rootScope, ProcessErrors, CheckLicense, moment, $timeout, Rest, LicenseStrings,
    $window, ConfigService, pendoService, insightsEnablementService, i18n, config, rhCreds, GetBasePath) {

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
            $scope.rhCreds = {};
            $scope.selectedLicense = {};
        };

        const initVars = (config) => {
            // license/license.partial.html compares fileName
            $scope.fileName = N_("No file selected.");

            if ($rootScope.licenseMissing) {
                $scope.title = $rootScope.BRAND_NAME + i18n._(" License");
            } else {
                $scope.title = i18n._("License Management");
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

            $scope.rhCreds = {};

            if (rhCreds.REDHAT_USERNAME && rhCreds.REDHAT_USERNAME !== "") {
                $scope.rhCreds.username = rhCreds.REDHAT_USERNAME;
            }

            if (rhCreds.REDHAT_PASSWORD && rhCreds.REDHAT_PASSWORD !== "") {
                $scope.rhCreds.password = rhCreds.REDHAT_PASSWORD;
                $scope.showPlaceholderPassword = true;
            }
        };

        const updateRHCreds = (config) => {
            Rest.setUrl(`${GetBasePath('settings')}system/`);
            Rest.get()
                .then(({data}) => {
                    initVars(config);

                    if (data.REDHAT_USERNAME && data.REDHAT_USERNAME !== "") {
                        $scope.rhCreds.username = data.REDHAT_USERNAME;
                    }

                    if (data.REDHAT_PASSWORD && data.REDHAT_PASSWORD !== "") {
                        $scope.rhCreds.password = data.REDHAT_PASSWORD;
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
            // readAsFoo runs async
            raw.onload = function() {
                try {
                    $scope.newLicense.file = JSON.parse(raw.result);
                } catch(err) {
                    ProcessErrors($rootScope, null, null, null,
                        {msg: i18n._('Invalid file format. Please upload valid JSON.')});
                }
            };

            try {
                raw.readAsText(event.target.files[0]);
            } catch(err) {
                ProcessErrors($rootScope, null, null, null,
                    {msg: i18n._('Invalid file format. Please upload valid JSON.')});
            }
        };

        // HTML5 spec doesn't provide a way to customize file input css
        // So we hide the default input, show our own, and simulate clicks to the hidden input
        $scope.fakeClick = function() {
            if($scope.user_is_superuser && (!$scope.rhCreds.username || $scope.rhCreds.username === '') && (!$scope.rhCreds.password || $scope.rhCreds.password === '')) {
                $('#License-file').click();
            }
        };

        $scope.downloadLicense = function() {
            $window.open('https://www.ansible.com/license', '_blank');
        };

        $scope.replacePassword = () => {
            if ($scope.user_is_superuser && !$scope.newLicense.file) {
                $scope.showPlaceholderPassword = false;
                $scope.rhCreds.password = "";
                $timeout(() => {
                    $('.tooltip').remove();
                    $('#rh-password').focus();
                });
            }
        };

        $scope.lookupLicenses = () => {
            if ($scope.rhCreds.username && $scope.rhCreds.password) {
                Wait('start');
                ConfigService.getSubscriptions($scope.rhCreds.username, $scope.rhCreds.password)
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
                return license.license_key === $scope.selectedLicense.modalKey;
            });
            $scope.selectedLicense.modalKey = undefined;
        };

        $scope.cancelLicenseLookup = () => {
            $scope.showLicenseModal = false;
            $scope.selectedLicense.modalKey = undefined;
        };

        $scope.submit = function() {
            Wait('start');
            let payload = {};
            if ($scope.newLicense.file) {
                payload = $scope.newLicense.file;
            } else if ($scope.selectedLicense.fullLicense) {
                payload = $scope.selectedLicense.fullLicense;
            }
            
            CheckLicense.post(payload, $scope.newLicense.eula)
                .then((licenseInfo) => {
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
                                updateRHCreds(config);
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
