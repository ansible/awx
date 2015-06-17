import systemTracking from 'tower/system-tracking/main';
import {describeModule} from '../describe-module';
import moment from 'tower/shared/moment/moment';

describeModule(systemTracking.name)
    .testService('factScanDataService', function(test, restStub) {

        var service;

        test.withService(function(_service) {
            service = _service;
        });

        it('returns list of versions with search parameters', function() {
            var version = { result: 'test' };
            var host_id = 1;
            var module = 'packages';
            var start = moment('2015-05-05');
            var end = moment('2015-05-06');
            var result = {
                data: {
                    results: [version]
                }
            };
            var actual, expected;

            var searchParams =
                {   hostId: host_id,
                    dateRange:
                    {   from: start,
                        to: end
                    },
                    endDate: end,
                    moduleName: module
                };

            actual = service.getVersion(searchParams);

            expected = _.clone(searchParams);
            expected.versions = [version];

            restStub.succeed(result);
            restStub.flush();

            return expect(actual).to.eventually.deep.equal(expected);

        });

        it('returns list of facts', function() {
            var facts = [{}],
            version = {
                "module" : "package",
                "timestamp": '2015-05-07T14:57:37',
                "related" : {
                    "fact_view" : "/hosts/1/fact_versions/?module=packages&from=2015-05-05T00:00:00-04:00&to=2015-05-06T00:00:00-04:00"
                }
            },
            result = {
                data: {
                    fact: facts
                }
            };

            var actual = service.getFacts(version)
                            .then(function(response) {
                                return response.fact;
                            });

            restStub.succeedAt(version.related.fact_view, result);
            restStub.flush();

            return expect(actual).to.eventually.equal(facts);

        });
    });
