import '../support/node';

import {describeModule} from '../support/describe-module';
import JobStatusGraph from '../../src/dashboard/graphs/job-status/main';

var processErrors = sinon.spy();

describeModule(JobStatusGraph.name)
    .mockProvider('ProcessErrors', processErrors)
    .testService('jobStatusGraphData', function(test, restStub) {
        var q;
        var service;

        var jobStatusChange = {
            $on: sinon.spy(),
        };

        beforeEach(inject(['$q', function($q) {
            q = $q;
        }]));

        test.withService(function(_service) {
            service = _service;
        });

        it('returns a promise to be fulfilled when data comes in', function() {
            var firstResult = "result";

            var result = service.get('', '');

            restStub.succeed({ data: firstResult });

            restStub.flush();

            return expect(result).to.eventually.equal(firstResult);;
        });

        it('processes errors through error handler', function() {
            var expected = { data: "blah", status: "bad" };
            var actual = service.get().catch(function() {
                return processErrors;
            });

            restStub.fail(expected);

            restStub.flush();

            return actual.catch(function() {
                expect(processErrors).to
                .have.been.calledWith(null, expected.data, expected.status);
            });

        });

        it('broadcasts event when data is received', function() {
            var expected = "value";
            var result = q.defer();
            service.setupWatcher();

            inject(['$rootScope', function($rootScope) {
                $rootScope.$on('DataReceived:JobStatusGraph', function(e, data) {
                    result.resolve(data);
                });
                $rootScope.$emit('JobStatusChange-home');
                restStub.succeed({ data: expected });
                restStub.flush();
            }]);

            return expect(result.promise).to.eventually.equal(expected);
        });

        it('requests data with given period and jobType', function() {
            restStub.setUrl = sinon.spy();

            service.get('1', '2');

            expect(restStub.setUrl).to.have.been.calledWith('/dashboard/graphs/jobs/?period=1&job_type=2');
        });
});
