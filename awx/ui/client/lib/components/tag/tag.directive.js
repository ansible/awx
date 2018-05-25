const templateUrl = require('~components/tag/tag.partial.html');

function atTag () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl,
        scope: {
            tag: '=',
            removeTag: '&?',
        },
    };
}

export default atTag;
