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

        // HACK: For some reason many of my divs
        // are ending up with a 1px size diff.
        // Guessing this is because of 3 cols
        // at 33% flex-basis, with 8px padding.
        // Perhaps the padding is pushing it over
        // in JavaScript but not visually? Using
        // threshold to filter those out.
        var threshold = 5;

        if(fullTextWidth > elementWidth &&
               fullTextWidth - elementWidth > threshold) {
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

    // HACK: This handles truncating _after_ other elements
    // are added that affect the size of this element. I
    // wanted to leave this as a regular event binding, but
    // was running into issues with the resized element getting
    // removed from the DOM after truncating! No idea why yet.
    element.resize(function() {
        addTitleIfWrapping(getText());
    });

    scope.$watch('$destroy', function() {
        element.off('resize');
    });
}

export default
    ['$compile',
        function($compile) {
            return {
                link: _.partial(link, $compile)
            };
        }
    ];
