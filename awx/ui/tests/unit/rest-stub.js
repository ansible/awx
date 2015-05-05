function assertUrlDeferred(url, obj) {
    if (angular.isUndefined(obj[url]) ||
        angular.isUndefined(obj[url].then) &&
            angular.isUndefined(obj[url].promise.then)) {
        var urls = [];

    for (var key in obj) {
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

function RestStub() {
}

RestStub.prototype =
    {   setUrl: function(url) {
            this[url] = this.$q.defer();
            this.currentUrl = url;
        },
        reset: function() {
            delete this.deferred;
        },
        get: function() {
            // allow a single deferred on this in case we don't need URL
            this.deferred = this[this.currentUrl];

            return this.deferred.promise;
        },
        destroy: function() {
            this.deferred = this.deferred || {};
            this.deferred.destroy = this[this.currentUrl];

            return this.deferred.destroy.promise;
        },
        succeedAt: function(url, value) {
            assertUrlDeferred(url, this);
            this[url].resolve(value);
        },
        succeedOn: function(method, value) {
            this.deferred[method] = value;
        },
        succeed: function(value) {
            this.deferred.resolve(value);
        },
        failAt: function(url, value) {
            assertUrlDeferred(url, this);
            this[url].reject(value);
        },
        fail: function(value) {
            this.deferred.reject(value);
        },
        flush: function() {
            window.setTimeout(function() {
                inject(['$rootScope', function($rootScope) {
                    $rootScope.$apply();
                }]);
            }, 1000);
        }
    };


export default RestStub;
