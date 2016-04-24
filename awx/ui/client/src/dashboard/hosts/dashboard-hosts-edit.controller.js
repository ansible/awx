/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
 	['$scope', '$state', '$stateParams', 'DashboardHostsForm', 'GenerateForm', 'host',
 	function($scope, $state, $stateParams, DashboardHostsForm, GenerateForm, host){
 		var generator = GenerateForm,
 			form = DashboardHostsForm;

 		var init = function(){
 			$scope.host = host;
 			GenerateForm.inject(form, {mode: 'edit', related: false, scope: $scope});
 		};

 		init();
 	}];