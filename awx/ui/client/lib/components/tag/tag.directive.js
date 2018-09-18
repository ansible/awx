const templateUrl = require('~components/tag/tag.partial.html');

function atTag () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl,
        scope: {
            tag: '=',
            icon: '@?',
            link: '@?',
            removeTag: '&?',
        },
    };
}

export default atTag;
