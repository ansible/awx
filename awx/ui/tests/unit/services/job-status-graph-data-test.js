describe('Job Status Graph Data Service', function() {

  var q;

  var jobStatusGraphData, httpBackend, rootScope, timeout;

  var jobStatusChange = {
    $on: sinon.spy(),
  };

  function flushPromises() {
    window.setTimeout(function() {
      inject(function($rootScope) {
        $rootScope.$apply();
      });
    }, 100);
  }

  var restStub = {
    setUrl: angular.noop,
    reset: function() {
      delete restStub.deferred;
    },
    get: function() {
      if (angular.isUndefined(restStub.deferred)) {
        restStub.deferred = q.defer();
      }

      return restStub.deferred.promise;
    },
    succeed: function(value) {
        restStub.deferred.resolve(value);
    },
    fail: function(value) {
      restStub.deferred.reject(value);
    }
  };

  beforeEach(module("Tower"));

  beforeEach(module(function($provide) {

    $provide.value("$cookieStore", { get: angular.noop });

    $provide.value('RestServices', restStub);
  }));

  afterEach(function() {
    restStub.reset();
  });

  beforeEach(inject(function(_jobStatusGraphData_, $httpBackend, $q, $rootScope, $timeout) {
    jobStatusGraphData = _jobStatusGraphData_;
    httpBackend = $httpBackend;
    rootScope = $rootScope;
    timeout = $timeout;
    $httpBackend.expectGET('/static/js/local_config.js').respond({
    });
    q = $q;
  }));

  it('returns a promise to be fulfilled when data comes in', function() {
    var firstResult = "result";

    var result = jobStatusGraphData.get('', '');

    restStub.succeed(firstResult);

    flushPromises();

    return expect(result).to.eventually.equal(firstResult);;
  });

  it('processes errors through error handler', function() {
    var expected = { data: "error", status: "bad" };
    var actual = jobStatusGraphData.get();

    restStub.fail(expected);

    flushPromises();

    return expect(actual).to.be.rejectedWith(expected);
  });

  it('broadcasts event when data is received', function() {
    var expected = "value";
    var result = q.defer();
    jobStatusGraphData.setupWatcher();

    inject(function($rootScope) {
      $rootScope.$on('DataReceived:JobStatusGraph', function(e, data) {
        result.resolve(data);
      });
      $rootScope.$emit('JobStatusChange');
      restStub.succeed(expected);
      flushPromises();
    });

    return expect(result.promise).to.eventually.equal(expected);
  });

});
