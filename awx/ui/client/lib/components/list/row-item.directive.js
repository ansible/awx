const templateUrl = require('~components/list/row-item.partial.html');

function atRowItem () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl,
        scope: {
            inline: '@',
            badge: '@',
            headerValue: '@',
            headerLink: '@',
            headerState: '@',
            headerTag: '@',
            secondaryTag: '@',
            status: '@',
            statusTip: '@',
            statusClick: '&?',
            labelValue: '@',
            labelState: '@',
            value: '@',
            valueLink: '@',
            valueBindHtml: '@',
            smartStatus: '=?',
            tagValues: '=?',
            // TODO: add see more for tags if applicable
            tagsAreCreds: '@'
        }
    };
}

export default atRowItem;
