import {describeModule} from 'tests/unit/describe-module';

var processErrors = sinon.spy();

describeModule('DashboardGraphs')
    .mockProvider('ProcessErrors', processErrors)
    .testService('hostCountGraphData', function(test, restStub) {

    var q;
    var service;

    beforeEach(inject(['$q', function($q) {
        q = $q;
    }]));


    test.withService(function(_service_) {
        service = _service_;
    });

    it('returns a promise to be fulfilled when data comes in', function() {
        var license = "license";
        var hostData = "hosts";

        var result = service.get();

        restStub.succeedAt('/config/', { data: {
            license_info: {
                instance_count: license
            }
        }
        });

        restStub.succeedAt('/dashboard/graphs/inventory/', { data: hostData });

        restStub.flush();

        return expect(result).to.eventually.eql({ license: license, hosts: hostData });;
    });

    it('processes errors through error handler', function() {
        var expected = { data: "blah", status: "bad" };
        var actual = service.get();

        restStub.failAt('/config/', expected);

        restStub.flush();

        return actual.catch(function() {
            expect(processErrors).to
            .have.been.calledWith(null, expected.data, expected.status);
        });

    });
    });

