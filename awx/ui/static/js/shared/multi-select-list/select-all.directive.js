// TODO: Extract to its own helper
// Example:
//      template('shared/multi-select-list/select-all')
//      // =>
//      '/static/js/shared/multi-select-list/select-all.html
//
function template(base) {
    return '/static/js/' + base + '.partial.html';
}

export default
    [   function() {
        return {
            require: '^multiSelectList',
            restrict: 'E',
            scope: {
                label: '@',
                itemsLength: '=',
                extendedItemsLength: '=',
                isSelectionExtended: '=',
                isSelectionEmpty: '=selectionsEmpty'
            },
            templateUrl: template('shared/multi-select-list/select-all'),
            link: function(scope, element, attrs, controller) {

                scope.label = scope.label || 'All';
                scope.selectExtendedLabel = scope.extendedLabel || 'Select all ' + scope.extendedItemsLength + ' items';
                scope.deselectExtendedLabel = scope.deselectExtendedLabel || 'Deselect extra items';

                scope.doSelectAll = function(e) {
                    if (scope.isSelected) {
                        controller.selectAll();

                        if (scope.supportsExtendedItems) {
                            scope.showExtendedMessage = scope.itemsLength !== scope.extendedItemsLength;
                        }
                    } else {
                        controller.deselectAll();
                    }
                };

                scope.$watch('extendedItemsLength', function(value) {
                    scope.supportsExtendedItems = _.isNumber(value);
                });

                scope.$watch('isSelectionEmpty', function(value) {
                    if (value) {
                        scope.isSelected = false;
                    }
                });

                scope.selectAllExtended = function() {
                    controller.selectAllExtended(scope.extendedItemsLength);
                };

                scope.deselectAllExtended = function() {
                    controller.deselectAllExtended(scope.extendedItemsLength);
                };

            }
        };
    }];
