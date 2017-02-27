/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

// import hostStatusBarController from './host-status-bar.controller';
export default [ 'templateUrl',
    function(templateUrl) {
    return {
        scope: true,
        templateUrl: templateUrl('job-results/host-status-bar/host-status-bar'),
        restrict: 'E',
        // controller: standardOutLogController,
        link: function(scope) {
            // as count is changed by event data coming in,
            // update the host status bar
            var toDestroy = scope.$watch('count', function(val) {
                if (val) {
                    Object.keys(val).forEach(key => {
                        // reposition the hosts status bar by setting
                        // the various flex values to the count of
                        // those hosts
                        $(`.HostStatusBar-${key}`)
                            .css('flex', `${val[key]} 0 auto`);

                        // set the tooltip to give how many hosts of
                        // each type
                        if (val[key] > 0) {
                            scope[`${key}CountTip`] = `<span class='HostStatusBar-tooltipLabel'>${key}</span><span class='badge HostStatusBar-tooltipBadge HostStatusBar-tooltipBadge--${key}'>${val[key]}</span>`;
                        }
                    });

                    // if there are any hosts that have finished, don't
                    // show default grey bar
                    scope.hasCount = (Object
                        .keys(val)
                        .filter(key => (val[key] > 0)).length > 0);
                }
            });

            scope.$on('$destroy', function(){
                toDestroy();
            });
        }
    };
}];
