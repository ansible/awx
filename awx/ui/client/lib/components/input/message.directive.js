const templateUrl = require('~components/input/message.partial.html');

function atInputMessage () {
    return {
        restrict: 'E',
        replace: true,
        templateUrl
    };
}

export default atInputMessage;
