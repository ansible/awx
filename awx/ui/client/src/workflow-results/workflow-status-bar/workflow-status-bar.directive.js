/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [ 'templateUrl',
    function(templateUrl) {
    return {
        scope: true,
        templateUrl: templateUrl('workflow-results/workflow-status-bar/workflow-status-bar'),
        restrict: 'E',
        link: function(scope) {
            // as count is changed by jobs coming in,
            // update the workflow status bar
            scope.$watch('count', function(val) {
                if (val) {
                    Object.keys(val).forEach(key => {
                        // reposition the workflow status bar by setting
                        // the various flex values to the count of
                        // those jobs
                        $(`.WorkflowStatusBar-${key}`)
                            .css('flex', `${val[key]} 0 auto`);

                        // set the tooltip to give how many jobs of
                        // each type
                        if (val[key] > 0) {
                            scope[`${key}CountTip`] = `<span class='WorkflowStatusBar-tooltipLabel'>${key}</span><span class='badge WorkflowStatusBar-tooltipBadge WorkflowStatusBar-tooltipBadge--${key}'>${val[key]}</span>`;
                        }
                    });

                    // if there are any hosts that have finished, don't
                    // show default grey bar
                    scope.hostsFinished = (Object
                        .keys(val)
                        .filter(key => (val[key] > 0)).length > 0);
                }
            });
        }
    };
}];
