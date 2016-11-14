/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {N_} from "../i18n";

export default
    ['Wait', '$state', '$scope', '$rootScope', '$location', 'GetBasePath',
    'Rest', 'ProcessErrors', 'CheckLicense', 'moment','$window',
    'ConfigService', 'FeaturesService', 'pendoService', 'i18n',
    function( Wait, $state, $scope, $rootScope, $location, GetBasePath, Rest,
        ProcessErrors, CheckLicense, moment, $window, ConfigService,
        FeaturesService, pendoService, i18n){

        var calcDaysRemaining = function(seconds){
	 		// calculate the number of days remaining on the license
			var duration = moment.duration(seconds, 'seconds').asDays();
			duration = Math.floor(duration);
            if(duration < 0 ){
                duration = 0;
            }
            duration = (duration!==1) ? `${duration} Days` : `${duration} Day`;
			return duration;
	 	};


        var calcExpiresOn = function(days){
            // calculate the expiration date of the license
            days = parseInt(days);
            return moment().add(days, 'days').calendar();
        };

        var reset = function(){
            document.getElementById('License-form').reset();
        };

        var init = function(){
            // license/license.partial.html compares fileName
            $scope.fileName = N_("No file selected.");
            $scope.title = $rootScope.licenseMissing ? ("Tower " + i18n._("License")) : i18n._("License Management");
            Wait('start');
            ConfigService.getConfig().then(function(config){
                $scope.license = config;
                $scope.license.version = config.version.split('-')[0];
                $scope.time = {};
                $scope.time.remaining = calcDaysRemaining($scope.license.license_info.time_remaining);
                $scope.time.expiresOn = calcExpiresOn($scope.time.remaining);
                $scope.valid = CheckLicense.valid($scope.license.license_info);
                $scope.compliant = $scope.license.license_info.compliant;
                Wait('stop');
            });
        };

        init();

        $scope.getKey = function(event){
            // Mimic HTML5 spec, show filename
            $scope.fileName = event.target.files[0].name;
            // Grab the key from the raw license file
            var raw = new FileReader();
            // readAsFoo runs async
            raw.onload = function(){
                try {
                    $scope.newLicense.file = JSON.parse(raw.result);
                }
                catch(err) {
                    ProcessErrors($rootScope, null, null, null, {msg: 'Invalid file format. Please upload valid JSON.'});
                }
            };
            try {
                raw.readAsText(event.target.files[0]);
            }
            catch(err) {
                ProcessErrors($rootScope, null, null, null, {msg: 'Invalid file format. Please upload valid JSON.'});
            }
        };
        // HTML5 spec doesn't provide a way to customize file input css
        // So we hide the default input, show our own, and simulate clicks to the hidden input
        $scope.fakeClick = function(){
            $('#License-file').click();
        };

        $scope.downloadLicense = function(){
            $window.open('https://www.ansible.com/license', '_blank');
        };

		$scope.newLicense = {};
		$scope.submit = function(){
			Wait('start');
			CheckLicense.post($scope.newLicense.file, $scope.newLicense.eula)
				.success(function(){
					reset();
                    ConfigService.delete();
                    ConfigService.getConfig().then(function(){
                        delete($rootScope.features);
                        FeaturesService.get();
                        pendoService.issuePendoIdentity();
                        if($rootScope.licenseMissing === true){
                            $state.go('dashboard', {
    							licenseMissing: false
    						});
    					}
    					else{
                            init();
    						$scope.success = true;
    						$rootScope.licenseMissing = false;
    						// for animation purposes
    						var successTimeout = setTimeout(function(){
    							$scope.success = false;
    							clearTimeout(successTimeout);
    						}, 4000);
    					}
                    });
			});
		};
     }
];
