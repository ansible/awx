export default
	['$scope', '$state', 'CheckLicense', function($scope, $state, CheckLicense){
		var processVersion = function(version){
					// prettify version & calculate padding
					// e,g 3.0.0-0.git201602191743/ -> 3.0.0
					var split = version.split('-')[0];
		            var spaces = Math.floor((16-split.length)/2),
		                paddedStr  = "";
		            for(var i=0; i<=spaces; i++){
		                paddedStr = paddedStr +" ";
		            }
		            paddedStr = paddedStr + split;
		            for(var j = paddedStr.length; j<16; j++){
		                paddedStr = paddedStr + " ";
		            }
		            return paddedStr;
		};
		var init = function(){
			CheckLicense.get()
				.then(function(res){
					$scope.subscription = res.data.license_info.subscription_name;
					$scope.version = processVersion(res.data.version);
					$('#about-modal').modal('show');
				});
		};
		$('#about-modal').on('hidden.bs.modal', function () {
		  $state.go('setup');
		});
		init();
	}
	];
