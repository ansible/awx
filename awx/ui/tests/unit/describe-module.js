import RestStub from 'tests/unit/rest-stub';

var $provide;

function wrapInjected(dslFn) {
    // wrapInjected(before(inject(..., function() {
    // }));
    return function(fn) {
        dslFn.apply(this,
            [inject(
            [   '$injector',
                function($injector) {
                    var $compile = $injector.get('$compile');
                    var $httpBackend = $injector.get('$httpBackend');
                    var $rootScope = $injector.get('$rootScope');

                    return fn.apply(this, [$httpBackend, $compile, $rootScope]);
                }.bind(this)
            ])]);
    };
};

function TestModule(name, deps) {

    window.localStorage.setItem('zones',    []);
    return {
        mockedProviders: {},
        registerPreHooks: function() {

                    var self = this;
                    beforeEach("tower module", module('Tower'));
                    beforeEach(name + " module", module(name));
                    beforeEach("templates module", module('templates'));
                    beforeEach("mock app setup", module(['$provide', function(_provide_) {

                       var getBasePath = function(path) {
                         return '/' + path + '/';
                       }

                        $provide = _provide_;
                        $provide.value('LoadBasePaths', angular.noop);
                        $provide.value('GetBasePath', getBasePath);

                        for (var name in self.mockedProviders) {
                            $provide.value(name, self.mockedProviders[name]);
                        }

                    }]));

                    wrapInjected(beforeEach)(function($httpBackend) {

                        $httpBackend
                            .expectGET('/static/js/local_config.js')
                            .respond({});
                });
            },
            mockProvider: function(name, value) {
                this.mockedProviders[name] = value;
            },
            describe: function(name, describeFn) {

                describe(name, function() {
                    describeFn.apply(this);
                });
            },
            registerPostHooks: function() {
                afterEach(inject(['$httpBackend', function($httpBackend) {
                    $httpBackend.verifyNoOutstandingExpectation();
                    $httpBackend.verifyNoOutstandingRequest();
                }]));
            }
    };
};

function TestService(name) {
    var restStub = new RestStub();

    afterEach(function() {
        restStub.reset();
    });

    return {
        withService: function(fn) {
            beforeEach(name + " service", inject([name, function() {
                var service = arguments[0];
                fn(service);
            }]));
        },
        restStub: restStub,
    };
};

// Note: if you need a compile step for your directive you
// must either:
//
// 1. Use a before/after compile hook, which also allows
//      you to modify the scope before compiling
// 2. If you don't use a hook, call `registerCompile`
//      prior to the first `it` in your tests
function TestDirective(name, deps) {

    return {   name: name,
            // Hooks that need to run after any hooks registered
            // by the test
            withScope: function(fn) {
                var self = this;
                beforeEach("capture outer $scope", inject(['$rootScope', function($rootScope) {
                    var $scope = self.$scope = self.$scope || $rootScope.$new();
                    // `this` refers to mocha test suite
                    fn.apply(this, [$scope]);
                }]));
            },
            withIsolateScope: function(fn) {
                var self = this;
                beforeEach("capture isolate scope", inject(['$rootScope', function($rootScope) {
                    // `this` refers to mocha test suite
                    fn.apply(this, [self.$element.isolateScope()]);
                }]));
            },
            beforeCompile: function(fn) {

                var self = this;

                // Run before compile step by passing in the
                // outer scope, allowing for modifications
                // prior to compiling
                self.withScope(fn);

                this.registerCompile();
            },
            afterCompile: function(fn) {

                var self = this;
                var $outerScope;

                // Make sure compile step gets setup first
                if (!this._compileRegistered) {
                    this.registerCompile();
                }

                // Then pre-apply the function with the outer scope
                self.withScope(function($scope) {
                    // `this` refers to mocha test suite
                    $outerScope = $scope;
                });

                // Finally, have it called by the isolate scope
                // hook, which will pass in both the outer
                // scope (since it was pre-applied) and the
                // isolate scope (if one exists)
                //
                self.withIsolateScope(function($scope) {
                    // `this` refers to mocha test suite
                    fn.apply(this, [$outerScope, $scope]);
                });

            },
            registerCompile: function(deps) {

                var self = this;

                // Only setup compile step once
                if (this._compileRegistered) {
                    return;
                }

                beforeEach("compile directive element",
                           inject(['$compile', '$httpBackend', '$rootScope', function($compile, $httpBackend, $rootScope) {

                    if (!self.$scope) {
                        self.$scope = $rootScope.$new();
                    }

                    self.$element = $compile(self.element)(self.$scope);
                    $(self.$element).appendTo('body');

                    self.$scope.$digest();

                    $httpBackend.flush();

                }]));

                afterEach("cleanup directive element", function() {
                    self.$element.trigger('$destroy');
                    self.$element.remove();
                });

                this._compileRegistered = true;

            },
            withController: function(fn) {
                var self = this;
                beforeEach(function() {
                    self._ensureCompiled();
                    fn(self.$element.controller(self.name));
                });
            },
            use: function(elem) {
                this.element = angular.element(elem);
            },
            provideTemplate: function(url, template) {
                var $scope = this.$scope;
                beforeEach("mock template endpoint", inject(['$httpBackend', function($httpBackend) {
                    $httpBackend
                        .whenGET(url)
                        .respond(template);
                }]));
            },
            _ensureCompiled: function() {
                if (typeof this.$element === 'undefined') {
                    throw "Can only call withController after registerPostHooks on directive test";
                }
            }
        };
}

function ModuleDescriptor(name, deps) {

    var moduleTests = [];
    var testModule =
        Object.create(TestModule(name, deps));

    var proto =
        {   mockProvider: function(name, value) {
                testModule.mockProvider(name, value);
                return this;
            },
            testService: function(name, test) {
                testModule.describe(name, function() {
                    var testService = Object.create(TestService(name));

                    testModule.mockProvider('Rest', testService.restStub);
                    testModule.mockProvider('$cookieStore', { get: angular.noop });
                    testModule.registerPreHooks();

                    beforeEach("$q", inject(['$q', function($q) {
                        testService.restStub.$q = $q;
                    }]));

                    test.apply(null, [testService, testService.restStub]);
                });
            },
            testDirective: function(name, test) {

                testModule.describe(name, function(deps) {
                    var directiveDeps = _.clone(deps);

                    var testDirective =
                        Object.create(TestDirective(name));

                    // Hand in testDirective object & injected
                    // dependencies to the test as separate arguments
                    //
                    var args = [testDirective].concat(_.values(directiveDeps));
                    var testObj =
                        // Using Function#bind to create a new function
                        // with the arguments pre-applied (go search
                        // the web for "partial application" to know more)
                        //
                        {   run: test.bind(null, testDirective, args),
                            name: name
                        };

                    testModule.registerPreHooks();

                    // testDirective.registerCompile();

                    testObj.run();

                    // testDirective.registerPostHooks();
                });
            }
    };

    return proto;
}

export function describeModule(name) {
    var descriptor = null
    descriptor = Object.create(ModuleDescriptor(name));


    return descriptor;
};
