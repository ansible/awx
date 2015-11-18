/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 *  @ngdoc overview
 *  @name multiSelectList
 *  @scope
 *  @description Does some stuff
 *
 *  @ngdoc directive
 *  @name multiSelectList.directive:multiSelectList
 *  @description
 *      The `multiSelectList` directive works in conjunction with the
 *      `selectListItem` and (optionally) the `selectAll` directives to
 *      render checkboxes with list items and tracking the selected state
 *      of each item. The `selectListItem` directive renders a checkbox,
 *      and the `multiSelectList` directive tracks the selected state
 *      of list items. The `selectAll` directive renders a checkbox that
 *      will select/deselect all items in the list.
 *
 *
 *      This directive exposes a special object on its local scope called
 *      `selection` that is used to access the current selection state.
 *      The following properties on `selection` are available:
 *
 *      | Property          | Type            | Details                                                      |
 *      |-------------------|-----------------|-------------------------------------------------------------|
 *      | `selectedItems`   | {@type array}   | The items that are currently selected                        |
 *      | `deselectedItem`  | {@type array}   | The items that are currently _not_ selected                  |
 *      | `isExtended`      | {@type boolean} | Indicates that the user has requested an extended selection |
 *      | `length`          | {@type number}  | The length of the selected items array                      |
 *
 *      Use the `multi-select-list` directive to indicate that you want
 *      to allow users to select items in a list. To display a checkbox
 *      next to each item, use the {@link multiSelectList.directive:selectListItem `select-list-item`} directive.
 *
 *      # Rendering a basic multi-select list
 *
 *      @example
 *
 *      This example creates a list of names and then
 *      uses `multiSelectList` to make the names
 *      selectable:
 *
       <example module="multiSelectList">
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
                     <li ng-repeat="item in names">
                       <select-list-item item="item"></select-list-item>
                       {{item.name}}
                     </li>
                   </ul>
               </div>
           </file>

      </example>

    # Making other elements respond to the state of the selction

    In this example, we'll see how to make a button that enables/disables
    itself based on some property of the selection.

    <example module="stateTrackingExample">
       <file name="controller.js">
            angular.module('stateTrackingExample', ['multiSelectList'])
                .controller('namesController', ['$scope', function($scope) {
                        $scope.names =
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

                        // Initial logic for buttons
                        $scope.noSelections = true;
                        $scope.atLeastOneSelection = false;
                        $scope.exactlyTwoSelections = false;

                        var cleanup = $scope.$on('multiSelectList.selectionChanged', function(e, selection) {
                            // Recalculate logic for buttons whenever selections change
                            $scope.noSelections = selection.length == 0;
                            $scope.atLeastOneSelection = selection.length >= 1;
                            $scope.exactlyTwoSelections = selection.length == 2;
                        });
                }]);
       </file>
       <file name="index.html">
           <div ng-controller="namesController">
               <button ng-if="noSelections">
                    Create
               </button>
               <button ng-if="atLeastOneSelection">
                    Delete
               </button>
               <button ng-if="exactlyTwoSelections">
                    Compare
               </button>
               <ul multi-select-list>
                 <li ng-repeat="item in names">
                   <select-list-item item="item"></select-list-item>
                   {{item.name}}
                 </li>
               </ul>
           </div>
       </file>

    </example>

 *
*/
import controller from './multi-select-list.controller';

export default
[   function() {
    return {
            restrict: 'A',
            scope: {
            },
            controller: controller
        };
    }];
