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

                scope.init();

            });
            $('#form-modal').modal('show');
        },
        controller: ['$scope', '$state', function($scope, $state) {

            $scope.init = function() {
                let list = $scope.list;
                if($state.params.selected) {
                    let selection = $scope[list.name].find(({id}) => id === parseInt($state.params.selected));
                    $scope.currentSelection = _.pick(selection, 'id', 'name');
                }
                $scope.$watch(list.name, function(){
                    selectRowIfPresent();
                });

                $scope.modalTitle = list.iterator.replace(/_/g, ' ');
            };

            function selectRowIfPresent(){
                let list = $scope.list;
                if($scope.currentSelection && $scope.currentSelection.id) {
                    $scope[list.name].forEach(function(row) {
                        if (row.id === $scope.currentSelection.id) {
                            row.checked = true;
                        }
                    });
                }
            }

            $scope.saveForm = function() {
                let list = $scope.list;
                if($scope.currentSelection.name !== null) {
                    $scope.$parent[`${list.iterator}_name`] = $scope.currentSelection.name;
                }
                $scope.$parent[list.iterator] = $scope.currentSelection.id;
                $state.go('^');
            };

            $scope.cancelForm = function() {
                $state.go('^');
            };

            $scope.toggle_row = function(selectedRow) {
                let list = $scope.list;
                let count = 0;
                $scope[list.name].forEach(function(row) {
                    if (row.id === selectedRow.id) {
                        if (row.checked) {
                            row.success_class = 'success';
                        } else {
                            row.checked = true;
                            row.success_class = '';
                        }
                        $scope.currentSelection = {
                            name: row.name,
                            id: row.id
                        };
                    } else {
                        row.checked = 0;
                        row.success_class = '';
                    }
                    if (row.checked) {
                        count++;
                    }
                });
            };

        }]
    };
}];
