const templateUrl = require('~components/cards/group.partial.html');

function atCardGroup () {
    return {
        restrict: 'E',
        transclude: true,
        templateUrl,
    };
}

export default atCardGroup;
