/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {N_} from "../i18n";

export default
    ['Wait', '$state', '$scope', '$rootScope', 'ProcessErrors', 'CheckLicense', 'moment', 'Rest', '$timeout',
    '$window', 'ConfigService', 'pendoService', 'insightsEnablementService', 'i18n', 'config', 'GetBasePath',
    function(Wait, $state, $scope, $rootScope, ProcessErrors, CheckLicense, moment, Rest, $timeout,
    $window, ConfigService, pendoService, insightsEnablementService, i18n, config, GetBasePath) {

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
            document.getElementById('License-form').reset();
            $scope.newLicense.eula = undefined;
            if (!$scope.licenseError) {
                $scope.rhCreds = {};
            }
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
            $scope.newLicense = {
                pendo: true,
                insights: true
            };

            $scope.rhCreds = {};
        };

        const init = (config) => {
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
        
        init(config);

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

        $scope.submit = function() {
            Wait('start');
            $scope.licenseError = false;
            let payload = {};
            if ($scope.newLicense.file) {
                payload = $scope.newLicense.file;
            } else if ($scope.rhCreds.username && $scope.rhCreds.password) {
                payload = {
                    rh_password: $scope.rhCreds.password,
                    rh_username: $scope.rhCreds.username
                };
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
                                init(config);
                                $scope.success = true;
                                $rootScope.licenseMissing = false;
                                // for animation purposes
                                const successTimeout = setTimeout(function() {
                                        $scope.success = false;
                                        clearTimeout(successTimeout);
                                }, 4000);
                            }
                        });
                }).catch((data) => {
                    Wait('stop');
                    $scope.licenseError = data.error;
                });
        };
}];
