/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
    [   '$window',
        AutoSizeModule
    ];

function AutoSizeModule($window) {

    // Adjusts the size of the module so that all modules
    // fit into a single a page; assumes there are 2 rows
    // of modules, with the available height being offset
    // by the navbar & the count summaries module
    return function(scope, element, attrs) {

        function adjustSize() {
            if (attrs.graphType === "hostStatus") {
                if (element.parent().width() > 596) {
                    element.height(285);//596);
                } else {
                    element.height(element.parent().width());
                }
            } else {
                element.height(285);
            }
        }

        $($window).resize(adjustSize);

        element.on('$destroy', function() {
            $($window).off('resize', adjustSize);
        });

        // This makes sure count-container div is loaded
        // by controllers/Home.js before we use it
        // to determine the available window height
        scope.$on('resizeGraphs', function() {
            adjustSize();
        });

    };

}
