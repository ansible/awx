/* jshint unused: vars */

function link($compile, scope, element, attrs) {

    function elementTextWillWrap(element) {
        var fullTextWidth = element[0].scrollWidth;
        var elementWidth = element.outerWidth();

        if(fullTextWidth > elementWidth) {
            return true;
        }

        return false;
    }

    function getText() {
        return element.text();
    }

    function addTitleIfWrapping(text) {
        if (elementTextWillWrap(element)) {
            element
                .addClass('u-truncatedText')
                .removeAttr('truncated-text')
                .attr('title', text);

            $compile(element)(scope);
        }
    }

    scope.$watch(getText, addTitleIfWrapping);
}

export default
    ['$compile',
        function($compile) {
            return {
                priority: 1000, // make sure this gets compiled
                               // before `title`
                link: _.partial(link, $compile)
            };
        }
    ];
