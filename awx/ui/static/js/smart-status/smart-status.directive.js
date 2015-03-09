import smartStatusController from 'tower/smart-status/smart-status.controller.js';
export default [ '$location', function($location) {
    return {
        restrict: 'E',
        link: function (scope){
            var str = scope.job_template.id+'_spark';
            scope[str].formatter = function(sparklines, options, point){
                return "<div class=\"smart-status-tooltip\"><span style=\"color: " + point.color + "\">&#9679;</span>" +
                  "Job id: " +
                  options.userOptions.tooltipValueLookups.jobs[point.offset] + "</div>" ;
            };

            $('aw-smart-status:eq('+scope.$index+')').sparkline(scope[str].sparkArray, {
                type: 'tristate',
                width: '4em',
                height: '2em',
                barWidth: 7,
                barSpacing: 2,
                zeroBarColor: 'grey',
                posBarColor: '#00aa00', //@green on ansible-ui
                negBarColor: '#aa0000', //@red
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

            $('aw-smart-status:eq('+scope.$index+')').bind('sparklineClick', function(ev) {
                var sparkline = ev.sparklines[0],
                    job = sparkline.getCurrentRegionFields(),
                    id;
                id = sparkline.options.userOptions.tooltipValueLookups.jobs[job.offset];
                location.href = '/#/jobs/' + id;
            });

        },
        controller: smartStatusController
    };
}];
