/* jshint unused: vars */

function link($compile, scope, element, attrs) {

    // If the element is a DOM comment, that means
    // it's been hidden with `ng-if` so don't try
    // to process it or we get an error!
    if (element[0].nodeType === 8) {
        element = element.next();

        // Element was removed due to `ng-if`, so don't
        // worry about it
        if (element.length === 0) {
            return;
        }
    }


    function elementTextWillWrap(element) {

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
                link: _.partial(link, $compile)
            };
        }
    ];
