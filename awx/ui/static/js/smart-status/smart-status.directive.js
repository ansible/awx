import smartStatusController from 'tower/smart-status/smart-status.controller.js';
export default [  function() {
    return {
        restrict: 'E',
        link: function (scope){
            var str = scope.job_template.id+'_smart';

            scope[str].formatter = function(sparklines, options, point){
                var status = options.userOptions.tooltipValueLookups.status[point.offset];
                //capitalize first letter
                status = status.charAt(0).toUpperCase() + status.slice(1);
                return "<div class=\"smart-status-tooltip\">Job ID: " +
                  options.userOptions.tooltipValueLookups.jobs[point.offset] +
                  "<br>Status: <span style=\"color: " + point.color + "\">&#9679;</span>"+status+"</div>" ;
            };

            $('aw-smart-status:eq('+scope.$index+')').sparkline(scope[str].sparkArray, {
                type: 'tristate',
                width: '4em',
                height: '2em',
                barWidth: 7,
                barSpacing: 2,
                zeroBarColor: 'grey',
                posBarColor: '#00aa00',
                negBarColor: '#aa0000',
                tooltipFormatter: scope[str].formatter,
                tooltipFormat: '{{value:jobs}}',
                tooltipValueLookups: {
                    jobs: scope[str].jobIds,
                    status: scope[str].smartStatus
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
