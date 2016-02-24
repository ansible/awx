/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
	[	'Wait', '$state', '$scope', '$location',
	 'GetBasePath', 'Rest', 'ProcessErrors', 'CheckLicense', 'moment',
	 function( Wait, $state, $scope, $location,
	 	GetBasePath, Rest, ProcessErrors, CheckLicense, moment){
	 	// codemirror
	 	var textArea = document.getElementById('License-codemirror');
		var editor = CodeMirror.fromTextArea(textArea, {
		   lineNumbers: true,
		   mode: 'json'
		});
		editor.on('blur', function(cm){
			$scope.newLicense.file = cm.getValue()
		});
		$scope.newLicense = {};
		$scope.submit = function(e){
			Wait('start')
			CheckLicense.post($scope.newLicense.file, $scope.newLicense.eula)
				.success(function(res){
					console.log(res)
			});
		}
	 	var calcDaysRemaining = function(ms){
	 		// calculate the number of days remaining on the license
	 		var duration = moment.duration(ms);
	 		return duration.days()
	 	}

	 	var calcExpiresOn = function(days){
	 		// calculate the expiration date of the license
	 		return moment().add(days, 'days').calendar()
	 	}
	 	Wait('start');
	 	CheckLicense.get()
	 		.then(function(res){
	 			$scope.license = res.data;
	 			$scope.time = {};
	 			$scope.time.remaining = calcDaysRemaining($scope.license.license_info.time_remaining);
	 			$scope.time.expiresOn = calcExpiresOn($scope.time.remaining);
	 			$scope.valid = CheckLicense.valid($scope.license.license_info);	 			
	 			Wait('stop');
	 		});
	}
	];