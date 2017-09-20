const templateUrl = require('~components/input/label.partial.html');

function atInputLabel () {
    return {
        restrict: 'E',
        replace: true,
        templateUrl
    };
}

export default atInputLabel;
