/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc object
 * @name multiSelectList.controller:multiSelectList
 *
 * @description
 *
 * `multiSelectList` controller provides the API for the {@link multiSelectList.directive:multiSelectList `multiSelectList`} directive. The controller contains methods for selecting/deselecting items, controlling the extended selection, registering items to be selectable and emitting an event on the directive's `$scope`.
 *
 */
export default ['$scope',
    function ($scope) {
        $scope.items = [];
        $scope.selection = {
            isExtended: false,
            selectedItems: [],
            deselectedItems: []
        };

        // Makes $scope.selection.length an alias for $scope.selectedItems.length
        Object.defineProperty($scope.selection,
                              'length',
                              {   get: function() {
                                  return this.selectedItems.length;
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

            /**
             *
             * @ngdoc event
             * @name multiSelectList.selectionChanged
             * @eventOf multiSelectList.directive:multiSelectList
             *
             */
            $scope.$emit('multiSelectList.selectionChanged', $scope.selection);
        }

        /**
         * @ngdoc
         * @name multiSelectList.controller:multiSelectList#registerItem
         * @methodOf multiSelectList.controller:multiSelectList
         *
         * @description
         * Prepares an object to be tracked in the select list. Returns the
         * decorated item created by
         * {@link multiSelectList.controller:multiSelectList#decorateItem `decorateItem`}
         */
        this.registerItem = function(item) {
            var decoratedItem = this.decorateItem(item);
            $scope.items = $scope.items.concat(decoratedItem);
            return decoratedItem;
        };

        /**
         * @ngdoc
         * @name multiSelectList.controller:multiSelectList#deregisterItem
         * @methodOf multiSelectList.controller:multiSelectList
         *
         * @description
         * Removes an item from the list; called if the item is removed from the display
         * so that it is no longer tracked as a selectable item.
         */
        this.deregisterItem = function(leavingItem) {
            $scope.items = $scope.items.filter(function(item) {
                return leavingItem !== item;
            });
            rebuildSelections();
        };

        /**
         * @ngdoc
         * @name multiSelectList.controller:multiSelectList#decorateItem
         * @methodOf multiSelectList.controller:multiSelectList
         *
         * @description
         *
         * This decorates an item with an object that has an `isSelected` property.
         * This value is used to determine the lists of selected and non-selected
         * items to emit with the `multiSelectList.selectionChanged`
         * event.
         */
        this.decorateItem = function(item) {
            return {
                isSelected: false,
                value: item
            };
        };

        /**
         * @ngdoc
         * @name multiSelectList.controller:multiSelectList#selectAll
         * @methodOf multiSelectList.controller:multiSelectList
         *
         * @description
         * Marks all items in the list as selected.
         * Triggers {@link multiSelectList.selectionChanged `multiSelectList.selectionChanged`}
         */
        this.selectAll = function() {
            $scope.items.forEach(function(item) {
                item.isSelected = true;
            });
            rebuildSelections();
        };

        /**
         * @ngdoc
         * @name multiSelectList.controller:multiSelectList#deselectAll
         * @methodOf multiSelectList.controller:multiSelectList
         *
         * @description
         * Marks all items in the list as not selected.
         * Triggers {@link multiSelectList.selectionChanged `multiSelectList.selectionChanged`}
         */
        this.deselectAll = function() {
          $scope.items.forEach(function(item) {
            item.isSelected = false;
          });
          $scope.selection.isExtended = false;
          rebuildSelections();
        };


        /**
         * @ngdoc
         * @name multiSelectList.controller:multiSelectList#deselectAllExtended
         * @methodOf multiSelectList.controller:multiSelectList
         *
         * @description
         * Disables extended selection.
         * Triggers {@link multiSelectList.selectionChanged `multiSelectList.selectionChanged`}
         */
        this.deselectAllExtended = function() {
            $scope.selection.isExtended = false;
            rebuildSelections();
        };

        /**
         * @ngdoc
         * @name multiSelectList.controller:multiSelectList#selectAllExtended
         * @methodOf multiSelectList.controller:multiSelectList
         *
         * @description
         * Enables extended selection.
         * Triggers {@link multiSelectList.selectionChanged `multiSelectList.selectionChanged`}
         */
        this.selectAllExtended = function() {
            $scope.selection.isExtended = true;
            rebuildSelections();
        };

        /**
         * @ngdoc
         * @name multiSelectList.controller:multiSelectList#selectItem
         * @methodOf multiSelectList.controller:multiSelectList
         *
         * @description
         * Marks an item as selected.
         * Triggers {@link multiSelectList.selectionChanged `multiSelectList.selectionChanged`}
         *
         */
        this.selectItem = function(item) {
            item.isSelected = true;
            rebuildSelections();
        };

        /**
         * @ngdoc
         * @name multiSelectList.controller:multiSelectList#deregisterItem
         * @methodOf multiSelectList.controller:multiSelectList
         *
         * @description
         * Marks an item as not selected.
         * Triggers {@link multiSelectList.selectionChanged `multiSelectList.selectionChanged`}
         *
         */
        this.deselectItem = function(item) {
            item.isSelected = false;
            rebuildSelections();
        };

    }];
