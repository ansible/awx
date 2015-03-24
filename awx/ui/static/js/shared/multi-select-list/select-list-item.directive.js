export default
    [   function() {
        return {
            restrict: 'E',
            scope: {
                item: '=item'
            },
            require: '^multiSelectList',
            template: '<input type="checkbox" ng-model="isSelected">',
            link: function(scope, element, attrs, multiSelectList) {

                scope.isSelected = false;
                scope.decoratedItem = multiSelectList.registerItem(scope.item);

                scope.$watch('isSelected', function(value) {
                    if (value === true) {
                        multiSelectList.selectItem(scope.decoratedItem);
                    } else if (value === false) {
                        multiSelectList.deselectItem(scope.decoratedItem);
                    }
                });

                scope.$watch('decoratedItem.isSelected', function(value) {
                    scope.isSelected = value;
                });

                scope.$on('$destroy', function() {
                    multiSelectList.deregisterItem(scope.decoratedItem);
                });

            }
        };
    }];
