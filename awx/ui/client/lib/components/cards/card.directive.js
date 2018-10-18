const templateUrl = require('~components/cards/card.partial.html');

function atCard () {
    return {
        restrict: 'E',
        transclude: true,
        templateUrl,
        scope: {
            title: '@',
        },
    };
}

export default atCard;
