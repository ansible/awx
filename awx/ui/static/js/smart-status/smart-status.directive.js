import smartStatusController from 'tower/smart-status/smart-status.controller.js';
export default [ function() {
    return {
        restrict: 'E',
        link: function (scope){ //}, element ){ //}, attr) {
            var str = scope.job_template.id+'_spark';
            // formatter: function(sparklines, options, point, recentJobs){
            //   if(point.x <= options.mergedOptions.CurrentTimeGroup)
            //     return "<div class=\"\"><span style=\"color: " + point.color + "\">&#9679;</span>" + options.get("tooltipValueLookups").names[point.x] + " - " + point.y + options.get("tooltipSuffix") + "</div>";
            //   else
            //     return "<div class=\"\"><span style=\"color: " + point.color + "\">&#9679;</span>" + options.get("tooltipValueLookups").names[point.x] + "</div>";
            // };

            $('aw-smart-status:eq('+scope.$index+')').sparkline(scope[str].sparkArray, {
                type: 'tristate',
                // tooltipFormatter: scope[str].formatter,
                tooltipFormat: '{{value:levels}}',
                tooltipValueLookups: {
                    levels: $.range_map({
                        '1': 'Success',
                        '-1': 'Failed',
                        '0' : 'Queued'
                        // '7:': 'High'
                    })
                }
            });
        },
        // templateUrl: 'static/js/smart-status/smart-status.partial.html',
        controller: smartStatusController
    };
}];
