/* jshint unused: vars */

export default function() {
    return function(scope, element, attrs) {
        if (attrs.awToolTip) {
            return;
        }

        element.tooltip();
    };
}

