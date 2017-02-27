export default
	['$scope', '$state', 'ConfigService', 'i18n',
        function($scope, $state, ConfigService, i18n){
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
			ConfigService.getConfig()
				.then(function(config){
					$scope.subscription = config.license_info.subscription_name;
					$scope.version = processVersion(config.version);
					$scope.version_str = i18n._("Version");
					$('#about-modal').modal('show');
				});
		};
		$('#about-modal').on('hidden.bs.modal', function () {
		  $state.go('setup');
		});
		init();
	}
	];
