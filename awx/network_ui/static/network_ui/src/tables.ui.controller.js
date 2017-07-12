

var TablesUIController = function($scope) {

    $scope.hello = "world";

    console.log("Tables UI started");

    $scope.$on('$destroy', function () {
        console.log("Tables UI stopping");
    });
};

exports.TablesUIController = TablesUIController;
console.log("Tables UI loaded");
