/* jshint unused: vars */

function link($compile, scope, element, attrs) {

    function elementTextWillWrap(element) {

        // If the element is a DOM comment, that means
        // it's been hidden with `ng-if` so don't try
        // to process it or we get an error!
        if (element[0].nodeType === 8) {
            return false;
        }

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
