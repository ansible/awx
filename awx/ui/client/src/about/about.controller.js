export default
	['$scope', '$state', 'ConfigService', 'AppStrings',
        function($scope, $state, ConfigService, AppStrings){
		var init = function(){
			$scope.name = AppStrings.get('BRAND_NAME');
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
