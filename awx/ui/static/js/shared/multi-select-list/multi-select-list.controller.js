export default ['$scope',
    function ($scope) {
        $scope.items = [];
        $scope.selection = {
            isExtended: false,
            selectedItems: [],
            deselectedItems: []
        };

        Object.defineProperty($scope.selection,
                              'length',
                              {   get: function() {
                                  return this.items.length;
                              }
                              });

        function rebuildSelections() {
            var _items = _($scope.items).chain();

            $scope.selection.selectedItems =
                _items.filter(function(item) {
                    return item.isSelected;
                }).pluck('value').value();

            $scope.selection.deselectedItems =
                _items.pluck('value').difference($scope.selection.selectedItems)
                    .value();

            $scope.$emit('multiSelectList.selectionChanged', $scope.selection);
        }

        this.registerItem = function(item) {
            var decoratedItem = this.decorateItem(item);
            $scope.items = $scope.items.concat(decoratedItem);
            return decoratedItem;
        };

        this.deregisterItem = function(leavingItem) {
            $scope.items = $scope.items.filter(function(item) {
                return leavingItem !== item;
            });
            rebuildSelections();
        };

        this.decorateItem = function(item) {
            return {
                isSelected: false,
                value: item
            };
        };

        this.selectAll = function() {
            $scope.items.forEach(function(item) {
                item.isSelected = true;
            });
        };

        this.deselectAll = function() {
          $scope.items.forEach(function(item) {
            item.isSelected = false;
          });
          $scope.selection.isExtended = false;
          rebuildSelections();
        };


        this.deselectAllExtended = function(extendedLength) {
            $scope.selection.isExtended = false;
        };

        this.selectAllExtended = function(extendedLength) {
            $scope.selection.isExtended = true;
        };

        this.selectItem = function(item) {
            item.isSelected = true;
            rebuildSelections();
        };

        this.deselectItem = function(item) {
            item.isSelected = false;
            rebuildSelections();
        };

    }];
