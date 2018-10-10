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
                item: '=item',
                disabled: '='
            },
            require: '^multiSelectList',
            template: '<input type="checkbox" data-multi-select-list-item ng-model="item.isSelected" ng-click="userInteractionSelect()" ng-disabled=disabled>',
            link: function(scope, element, attrs, multiSelectList) {

                scope.decoratedItem = multiSelectList.registerItem(scope.item);

                scope.$watch('item.isSelected', function(value) {
                    if (value === true) {
                        multiSelectList.selectItem(scope.decoratedItem);
                    } else if (value === false) {
                        multiSelectList.deselectItem(scope.decoratedItem);
                    }
                });

                scope.userInteractionSelect = function() {
                    scope.$emit("selectedOrDeselected", scope.decoratedItem);
                };

            }
        };
    }];
