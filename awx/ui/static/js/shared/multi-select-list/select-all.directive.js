/**
 * @ngdoc directive
 * @name multiSelectList.directive:selectAll
 * @scope
 * @restrict E
 *
 * @param {string} label The text that will appear next to the checkbox
 * @param {number} itemsLength The number of displayed items in the list
 * @param {number} extendedItemsLength The total number of items in the list used for extended mode (see below)
 * @param {string_expression} extendedLabel A custom label to display when prompting the user to extend the selection; this is an expression so strings must be in single quotes ('), but you can use scope varibles here to display the count of items with the `extendedItemsLength` property
 * @param {boolean_expression} selectionsEmpty An expression that evaluates to a truthy value used to disable
 *                                              the select all checkbox when the displayed list is empty
 *
 * @description
 *
 * Use the `select-all` directive as a child of a `multi-select-list`
 * to present the user with a checkbox that, when checked, checks all
 * `select-list-item` children, and when unchecked it unchecks them.
 *
 * <example module="multiSelectList">
       <file name="index.html">
           <div ng-init="names =
                  [ { name: 'blah'
                    },
                    { name: 'diddy'
                    },
                    { name: 'doo'
                    },
                    { name: 'dah'
                    },
                    { name: 'blah'
                    }
                  ]">
               <ul multi-select-list>
                 <li>
                    <select-all label="Select All"></select-all>
                 </li>
                 <li ng-repeat="item in names">
                   <select-list-item item="item"></select-list-item>
                   {{item.name}}
                 </li>
               </ul>
           </div>
       </file>

 * </example>
 *
 * ## Extended Selections
 *
 * In some cases the list items you are displaying are only a subset of
 * a larger list (eg. using pagination or infinite scroll to seperate
 * items). In these cases, when a user checks "select all", it may be
 * useful to give them the option to also select all the remaining
 * items in the list.
 *
 * This behavior is controlled by the `extendedItemsLength` property
 * of this directive. Set it to the total length of items in the list.
 * For example, if you have a list of 100 items, displayed 10 per page,
 * then `itemsLength` would be 10 and `extendedItemsLength` would be 100.
 * When the user checks "select all" in the above example, it will show
 * a button prompting them to "Select all 100 items". When the user selects
 * this option, the `select-all` directive tells the `multiSelectList`
 * controller that the selection is "extended" to all the items in the list.
 * Listeners to the `multiSelectList.selectionChanged` event can then use this
 * flag to respond differently when all items are selected.
 *
 *
 * <example module="extendedSelectionExample">
        <file name="app.js">
            angular.module('extendedSelectionExample', ['multiSelectList'])
                .controller('namesController', ['$scope', function($scope) {

                        var cleanup = $scope.$on('multiSelectList.selectionChanged', function(e, selection) {
                            $scope.isSelectionExtended = selection.isExtended;
                        });

                       $scope.$on('$destroy', cleanup);

                       $scope.allNames =
                         [ { name: 'John'
                           },
                           { name: 'Jared'
                           },
                           { name: 'Joe'
                           },
                           { name: 'James'
                           },
                           { name: 'Matt'
                           },
                           { name: 'Luke'
                           },
                           { name: 'Chris'
                           }
                         ];

                       $scope.firstPageOfNames =
                           $scope.allNames.slice(0,3);
                }]);
        </file>
       <file name="index.html">
           <div ng-controller="namesController">
                <p ng-if="isSelectionExtended">Extended Selection</p>
               <ul multi-select-list>
                 <li>
                    <select-all
                      label="Select All"
                      selections-empty="selectedItems.length === 0"
                      extended-items-length="allNames.length"
                      items-length="firstPageOfNames.length"></select-all>
                 </li>
                 <li ng-repeat="item in firstPageOfNames">
                   <select-list-item item="item"></select-list-item>
                   {{item.name}}
                 </li>
               </ul>
           </div>
       </file>
 *</example>
 */
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
                extendedLabel: '&',
                isSelectionEmpty: '=selectionsEmpty'
            },
            templateUrl: template('shared/multi-select-list/select-all'),
            link: function(scope, element, attrs, controller) {

                scope.label = scope.label || 'All';
                scope.selectExtendedLabel = scope.extendedLabel() || 'Select all ' + scope.extendedItemsLength + ' items';
                scope.deselectExtendedLabel = scope.deselectExtendedLabel || 'Deselect extra items';

                scope.doSelectAll = function(e) {
                    if (scope.isSelected) {
                        controller.selectAll();

                        if (scope.supportsExtendedItems) {
                            scope.showExtendedMessage = scope.itemsLength !== scope.extendedItemsLength;
                        }
                    } else {
                        controller.deselectAll();

                        if (scope.isSelectionExtended) {
                            scope.deselectAllExtended();
                        }

                        scope.showExtendedMessage = false;
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
                    scope.isSelectionExtended = true;
                };

                scope.deselectAllExtended = function() {
                    controller.deselectAllExtended(scope.extendedItemsLength);
                    scope.isSelectionExtended = false;
                };

            }
        };
    }];
