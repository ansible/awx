/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    [   '$scope',
        function($scope) {

            let updateInventoryList = function() {
                $scope.inventories.forEach((row, i) => {
                    $scope.inventories[i].checked = 0;
                    if (row.id === $scope.selectedInventory.id) {
                        $scope.inventories[i].checked = 1;
                    }
                });
            };

            let uncheckAllInventories = function() {
                $scope.inventories.forEach((row, i) => {
                    $scope.inventories[i].checked = 0;
                });
            };

            let init = function() {
                $scope.$watch('selectedInventory', () => {
                    if($scope.inventories && $scope.inventories.length > 0) {
                        if($scope.selectedInventory) {
                            updateInventoryList();
                        }
                        else {
                            uncheckAllInventories();
                        }
                    }
                });
            };

            init();

            $scope.toggle_row = function(selectedRow) {
                let list = $scope.list;
                let count = 0;
                $scope[list.name].forEach(function(row) {
                    if (row.id === selectedRow.id) {
                        if (row.checked) {
                            row.success_class = 'success';
                        } else {
                            row.checked = 1;
                            row.success_class = '';
                        }
                        $scope.$emit('inventorySelected', row);
                    } else {
                        row.checked = 0;
                        row.success_class = '';
                    }
                    if (row.checked) {
                        count++;
                    }
                });
            };
        }
    ];
