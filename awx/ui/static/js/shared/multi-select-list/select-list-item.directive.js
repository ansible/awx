/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc directive
 * @name multiSelectList.directive:selectListItem
 * @restrict E
 * @scope
 * @description
 *
    The `select-list-item` directive renders a checkbox for tracking
    the state of a given item in a list. When the user checks the
    checkbox it tells the `multi-select-list` controller to select
    the item; when the user unchecks the checkbox it tells the controller
    to deselect the item.

    @example

    For examples of using this directive, see {@link multiSelectList.directive:multiSelectList multiSelectList}.

 */
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
