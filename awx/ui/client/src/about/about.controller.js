export default
	['$scope', '$state', 'ConfigService', 'i18n',
        function($scope, $state, ConfigService, i18n){
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
