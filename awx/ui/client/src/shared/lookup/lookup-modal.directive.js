export default ['templateUrl', function(templateUrl) {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        scope: false,
        templateUrl: templateUrl('shared/lookup/lookup-modal'),
        link: function(scope, element, attrs, controller, transcludefn) {

            transcludefn(scope, (clone, linked_scope) => {
                // scope.$resolve is a reference to resolvables in stateDefinition.resolve block
                // https://ui-router.github.io/docs/latest/interfaces/state.statedeclaration.html#resolve
                let list = linked_scope.$resolve.ListDefinition,
                    Dataset = linked_scope.$resolve.Dataset;
                // search init
                linked_scope.list = list;
                linked_scope[`${list.iterator}_dataset`] = Dataset.data;
                linked_scope[list.name] = linked_scope[`${list.iterator}_dataset`].results;

                element.find('.modal-body').append(clone);

            });
            $('#form-modal').modal('show');
        },
        controller: ['$scope', '$state', function($scope, $state) {
            $scope.saveForm = function() {
                let list = $scope.list;
                $scope.$parent[`${list.iterator}_name`] = $scope.selection[list.iterator].name;
                $scope.$parent[list.iterator] = $scope.selection[list.iterator].id;
                $state.go('^');
            };
            $scope.cancelForm = function() {
                $state.go('^');
            };
        }]
    };
}];
