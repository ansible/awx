export default function() {
    return {
        restrict: 'E',
        templateUrl: '/static/js/shared/icon/icon.partial.html',
        scope: {
        },
        link: function(scope, element, attrs) {
            var svg = $('svg', element);
            var iconPath = '#' + attrs.name;

            // Make a copy of the <symbol> tag to insert its contents into this
            // element's svg tag
            var content = $(iconPath).clone();

            // Copy classes off the <symbol> so that we preserve any styling
            // when we copy the item inline
            var classes = $(iconPath).attr('class');

            svg.attr('class', classes)
                .html(content.contents());

        }
    };
}
