import smartStatusController from 'tower/smart-status/smart-status.controller.js';
export default [  function() {
    return {
        scope: {
            jobs: '='
        },
        restrict: 'E',
        link: function (scope, element){

            scope.formatter = function(sparklines, options, point){
                var status = options.userOptions.tooltipValueLookups.status[point.offset];
                //capitalize first letter
                status = status.charAt(0).toUpperCase() + status.slice(1);
                return "<div class=\"smart-status-tooltip\">Job ID: " +
                  options.userOptions.tooltipValueLookups.jobs[point.offset] +
                  "<br>Status: <span style=\"color: " + point.color + "\">&#9679;</span>"+status+"</div>" ;
            };

            element.sparkline(scope.sparkArray, {
                type: 'tristate',
                width: '4em',
                height: '2em',
                barWidth: 7,
                barSpacing: 2,
                zeroBarColor: 'grey',
                posBarColor: '#00aa00',
                negBarColor: '#aa0000',
                tooltipFormatter: scope.formatter,
                tooltipFormat: '{{value:jobs}}',
                tooltipValueLookups: {
                    jobs: scope.jobIds,
                    status: scope.smartStatus
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
