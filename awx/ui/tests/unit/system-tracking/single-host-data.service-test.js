import systemTracking from 'tower/system-tracking/main';
import {describeModule} from '../describe-module';
import moment from 'tower/shared/moment/moment';

describeModule(systemTracking.name)
    .testService('factScanDataService', function(test, restStub) {

        var service;

        test.withService(function(_service) {
            service = _service;
        });

        it('returns list of versions', function() {
            var version = [{}],
            host_id = 1,
            module = 'packages',
            start = moment('2015-05-05'),
            end = moment('2015-05-06'),
            result = {
                data: {
                    results: version
                }
            };

            var actual = service.getVersion(host_id, module, start, end);

            restStub.succeed(result);
            restStub.flush();

            return expect(actual).to.eventually.equal(version[0]);

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
