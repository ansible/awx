

var TablesUIController = function($scope, $window) {

    $window.scope = $scope;

    $scope.user = {
        name: 'world'
    };

    $scope.data = [['A', 'B', 'C'],
    ['1', 1,2,3], ['2', 4,5,6], ['3', 7,8,9]];

    console.log("Tables UI started");

    $scope.$on('$destroy', function () {
        console.log("Tables UI stopping");
    });

    $scope.updateData = function (old_data, new_data, column_index, row_index, column_name, row_name) {
        console.log(['updateData', old_data, new_data, column_index, row_index, column_name, row_name]);
    };
};

exports.TablesUIController = TablesUIController;
console.log("Tables UI loaded");
