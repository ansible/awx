/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
 	['$scope', 'HostsService',
 	function($scope, HostsService){

        function codemirror () {
            return {
                init:{}
            };
        }
        $scope.codeMirror = new codemirror();
 		$scope.formCancel = function(){
            $scope.$parent.$broadcast('awxNet-closeDetailsPanel');
 		};

 		$scope.formSave = function(){
 			var host = {
 				id: $scope.item.id,
 				variables: $scope.variables === '---' || $scope.variables === '{}' ? null : $scope.variables,
 				name: $scope.item.name,
 				description: $scope.item.description,
 				enabled: $scope.item.enabled
 			};
 			HostsService.put(host).then(function(response){
                $scope.saveConfirmed = true;
                if(_.has(response, "data")){
                    $scope.$parent.$broadcast('awxNet-hostUpdateSaved', response.data);
                }
                setTimeout(function(){
                    $scope.saveConfirmed = false;
                }, 3000);
 			});
 		};

        $scope.$parent.$on('awxNet-showDetails', (e, data, canAdd) => {
            if (!_.has(data, 'host_id')) {
                $scope.item = data;
                $scope.canAdd = canAdd;
            } else {
                $scope.item = data;
            }
            if ($scope.codeMirror.init) {
                $scope.codeMirror.init($scope.item.variables);
            }
        });
 	}];
