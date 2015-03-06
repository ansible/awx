import smartStatusController from 'tower/smart-status/smart-status.controller.js';
export default [ function() {
    return {
        restrict: 'E',
        link: function (scope){ //}, element ){ //}, attr) {
            var str = scope.job_template.id+'_spark';
            scope[str].formatter = function(sparklines, options, point){
                return "<div class=\"smart-status-tooltip\"><span style=\"color: " + point.color + "\">&#9679;</span>" +
                  options.userOptions.tooltipValueLookups.jobs[point.offset] + "</div>";
            };

            $('aw-smart-status:eq('+scope.$index+')').sparkline(scope[str].sparkArray, {
                type: 'tristate',
                width: '4em',
                height: '2em',
                barWidth: 5,
                barSpacing: 2,
                tooltipFormatter: scope[str].formatter,
                tooltipFormat: '{{value:jobs}}',
                tooltipValueLookups: {
                    jobs: scope[str].jobIds
                    // $.range_map({
                    //     '1': 'Success',
                    //     '-1': 'Failed',
                    //     '0' : 'Queued'
                    //     // '7:': 'High'
                    // })
                }
            });
        },
        // templateUrl: 'static/js/smart-status/smart-status.partial.html',
        controller: smartStatusController
    };
}];
