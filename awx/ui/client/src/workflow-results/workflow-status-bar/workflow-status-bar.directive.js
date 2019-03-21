/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [ 'templateUrl', 'OutputStrings',
    function(templateUrl, OutputStrings) {
    return {
        scope: true,
        templateUrl: templateUrl('workflow-results/workflow-status-bar/workflow-status-bar'),
        restrict: 'E',
        link: function(scope) {
            scope.strings = OutputStrings;
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

                        let tooltipLabel = key;

                        switch(key) {
                            case 'successful':
                                tooltipLabel = scope.strings.get('workflow_status.SUCCESSFUL');
                                break;
                            case 'failed':
                                tooltipLabel = scope.strings.get('workflow_status.FAILED');
                                break;
                            }

                        // set the tooltip to give how many jobs of
                        // each type
                        if (val[key] > 0) {
                            scope[`${key}CountTip`] = `<span class='WorkflowStatusBar-tooltipLabel'>${tooltipLabel}</span><span class='badge WorkflowStatusBar-tooltipBadge WorkflowStatusBar-tooltipBadge--${key}'>${val[key]}</span>`;
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
