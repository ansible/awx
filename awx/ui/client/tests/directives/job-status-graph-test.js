/* jshint node: true */

import '../support/node';

import {describeModule} from '../support/describe-module';
import '../../src/shared/Utilities';
import '../../src/shared/RestServices';
import JobStatusGraph from '../../src/dashboard/graphs/job-status/main';

var resizeHandler = sinon.spy();

window.$.fn.removeResize = angular.noop;

describeModule(JobStatusGraph.name)
    .mockProvider('adjustGraphSize', resizeHandler)
    .mockProvider('Wait', angular.noop)
    .mockProvider('Rest', angular.noop)
    .testDirective('jobStatusGraph', function(directive) {


        directive.provideTemplate(
            '/static/partials/job_status_graph.html',
            "<div class='m'></div><div class='n'></div><div class='job-status-graph'><svg></svg></div>");

        directive.use('<job-status-graph class="job-status-graph" data="data" job-type="all" period="month"></job-status-graph>');

        directive.beforeCompile(function($scope) {

            // Takes jobs grouped by result (successful or failure
            //  Then looks at each array of arrays, where index 0 is the timestamp & index 1 is the count of jobs with that status
            $scope.data =
              { jobs:
                  { successful: [[1, 0], [2, 0], [3,0], [4,0], [5,0]],
                    failed: [[1,0],[2,0],[3,0],[4,0],[5,0]]
                  }
              };

        });

        function filterDataSeries(key, data) {
            return data.map(function(datum) {
                return datum.values;
            })[key];
        }

        it('uses successes & failures from scope', function() {
            var chartContainer = d3.select(directive.$element.find('svg')[0]);
            var lineData = chartContainer.datum();

            var successfulSeries = filterDataSeries(0, lineData);
            var failedSeries = filterDataSeries(1, lineData);

            expect(successfulSeries).to.eql(
                [   {x: 1, y: 0, series: 0},
                    {x: 2, y: 0, series: 0},
                    {x: 3, y: 0, series: 0},
                    {x: 4, y: 0, series: 0},
                    {x: 5, y: 0, series: 0}
                ]);

            expect(failedSeries).to.eql(
                [   {x: 1, y: 0, series: 1},
                    {x: 2, y: 0, series: 1},
                    {x: 3, y: 0, series: 1},
                    {x: 4, y: 0, series: 1},
                    {x: 5, y: 0, series: 1}
                ]);

        });

        it('cleans up external bindings', function() {
            directive.$element.trigger('$destroy');

            resizeHandler.reset();

            inject(['$window', function($window) {
                angular.element($window).trigger('resize');
            }]);

            expect(resizeHandler).not.to.have.been.called;
        });

    });
