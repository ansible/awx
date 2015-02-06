describe('Host Count Graph Data Service', function() {

  var q;

  var hostCountGraphData, httpBackend, rootScope, timeout;

  var processErrors = sinon.spy();

  var getBasePath = function(path) {
    return '/' + path + '/';
  }

  function flushPromises() {
    window.setTimeout(function() {
      inject(function($rootScope) {
        $rootScope.$apply();
      }, 1000);
    });
  }

  function assertUrlDeferred(url, obj) {
    if (angular.isUndefined(obj[url]) ||
          angular.isUndefined(obj[url].then) &&
            angular.isUndefined(obj[url].promise.then)) {
      var urls = [];

      for (key in obj) {
        if (/\//.test(key)) {
          urls.push(key);
        }
      }

      var registered = urls.map(function(url) {
        return "\t\"" + url + "\"";
      }).join("\n");

      throw "Could not find a thenable registered for url \"" + url + "\". Registered URLs include:\n\n" + registered + "\n\nPerhaps you typo'd the URL?\n"
    }
  }

  var restStub = {
    setUrl: function(url) {
      restStub[url] = q.defer();
      restStub.currentUrl = url;
    },
    reset: function() {
      delete restStub.deferred;
    },
    get: function() {
      // allow a single deferred on restStub in case we don't need URL
      restStub.deferred = restStub[restStub.currentUrl];

      return restStub.deferred.promise;
    },
    succeedAt: function(url, value) {
      assertUrlDeferred(url, restStub);
      restStub[url].resolve(value);
    },
    succeed: function(value) {
      restStub.deferred.resolve(value);
    },
    failAt: function(url, value) {
      assertUrlDeferred(url, restStub);
      restStub[url].reject(value);
    },
    fail: function(value) {
      restStub.deferred.reject(value);
    }
  };

  beforeEach(module("Tower"));

  beforeEach(module(function($provide) {

    $provide.value("$cookieStore", { get: angular.noop });

    $provide.value('ProcessErrors', processErrors);
    $provide.value('Rest', restStub);
    $provide.value('GetBasePath', getBasePath);
  }));

  afterEach(function() {
    restStub.reset();
  });

  beforeEach(inject(function(_hostCountGraphData_, $httpBackend, $q, $rootScope, $timeout) {
    hostCountGraphData = _hostCountGraphData_;
    httpBackend = $httpBackend;
    rootScope = $rootScope;
    timeout = $timeout;
    $httpBackend.expectGET('/static/js/local_config.js').respond({
    });
    q = $q;
  }));

  it('returns a promise to be fulfilled when data comes in', function() {
    var license = "license";
    var hostData = "hosts";

    var result = hostCountGraphData.get();

    restStub.succeedAt('/config/', { data: {
      license_info: {
        instance_count: license
      }
    }
    });

    restStub.succeedAt('/dashboard/graphs/inventory/', { data: hostData });

    flushPromises();

    return expect(result).to.eventually.eql({ license: license, hosts: hostData });;
  });

  it('processes errors through error handler', function() {
    var expected = { data: "blah", status: "bad" };
    var actual = hostCountGraphData.get();

    restStub.failAt('/config/', expected);

    flushPromises();

    return actual.catch(function() {
      expect(processErrors).to
        .have.been.calledWith(null, expected.data, expected.status);
    });

  });

});

