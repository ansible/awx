export default
	['$scope', '$state', 'ConfigService',
        function($scope, $state, ConfigService){
		var init = function(){
			ConfigService.getConfig()
				.then(function(config){
					$scope.version = config.version.split('-')[0];
					$scope.ansible_version = config.ansible_version;
					$scope.subscription = config.license_info.subscription_name;
					$('#about-modal').modal('show');
				});
		};
		$('#about-modal').on('hidden.bs.modal', function () {
		  $state.go('setup');
		});
		init();
	}
	];
