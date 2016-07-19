import '../support/node';

import adhocModule from 'inventories/manage/adhoc/main';
import RestStub from '../support/rest-stub';

describe("adhoc.controller", function() {
    var $scope, $rootScope, $location, $stateParams, $stateExtender,
        CheckPasswords, PromptForPasswords, CreateLaunchDialog, AdhocForm,
        GenerateForm, Rest, ProcessErrors, ClearScope, GetBasePath, GetChoices,
        KindChange, LookUpInit, CredentialList, Empty, Wait;

    var $controller, ctrl, generateFormCallback, waitCallback, locationCallback,
        getBasePath, processErrorsCallback, restCallback, stateExtenderCallback;

    beforeEach("instantiate the adhoc module", function() {
        angular.mock.module(adhocModule.name);
    });

    before("create spies", function() {
        getBasePath = function(path) {
            return '/' + path + '/';
        };
        generateFormCallback = {
            inject: angular.noop
        };
        waitCallback = sinon.spy();
        locationCallback = {
            path: sinon.spy()
        };
        processErrorsCallback = sinon.spy();
        restCallback = new RestStub();
        stateExtenderCallback = {
            addState: angular.noop
        }
    });


    beforeEach("mock dependencies", angular.mock.module(['$provide', function(_provide_) {
        var $provide = _provide_;

        $provide.value('$location', locationCallback);
        $provide.value('CheckPasswords', angular.noop);
        $provide.value('PromptForPasswords', angular.noop);
        $provide.value('CreateLaunchDialog', angular.noop);
        $provide.value('AdhocForm', angular.noop);
        $provide.value('GenerateForm', generateFormCallback);
        $provide.value('Rest', restCallback);
        $provide.value('ProcessErrors', processErrorsCallback);
        $provide.value('ClearScope', angular.noop);
        $provide.value('GetBasePath', getBasePath);
        $provide.value('GetChoices', angular.noop);
        $provide.value('KindChange', angular.noop);
        $provide.value('LookUpInit', angular.noop);
        $provide.value('CredentialList', angular.noop);
        $provide.value('Empty', angular.noop);
        $provide.value('Wait', waitCallback);
        $provide.value('$stateExtender', stateExtenderCallback);
        $provide.value('$stateParams', angular.noop);
        $provide.value('$state', angular.noop);
    }]));

    beforeEach("put the controller in scope", inject(function($rootScope, $controller) {
        var scope = $rootScope.$new();
        ctrl = $controller('adhocController', {$scope: scope});
    }));

    beforeEach("put $q in scope", window.inject(['$q', function($q) {
        restCallback.$q = $q;
    }]));
    /*
    describe("setAvailableUrls", function() {
        it('should only have the specified urls ' +
            'available for adhoc commands', function() {
                var urls = ctrl.privateFn.setAvailableUrls();
                expect(urls).to.have.keys('adhocUrl', 'inventoryUrl',
                    'machineCredentialUrl');

                var count = 0;
                var i;

                for (i in urls) {
                    if (urls.hasOwnProperty(i)) {
                        count++;
                    }
                }
                expect(count).to.equal(3);
            });

    });

    describe("setFieldDefaults", function() {
        it('should set the select form field defaults' +
            'based on user settings', function() {
                var verbosity_options = [
                        {label: "0 (Foo)", value: 0, name: "0 (Foo)",
                            isDefault: false},
                        {label: "1 (Bar)", value: 1, name: "1 (Bar)",
                            isDefault: true},
                    ],
                    forks_field = {};

                forks_field.default = 3;

                $scope.$apply(function() {
                    ctrl.privateFn.setFieldDefaults(verbosity_options,
                        forks_field.default);
                });

                expect($scope.forks).to.equal(forks_field.default);
                expect($scope.verbosity.value).to.equal(1);
            });
    });

    describe("setLoadingStartStop", function() {
        it('should start the controller working state when the form is ' +
            'loading', function() {
                waitCallback.reset();
                ctrl.privateFn.setLoadingStartStop();
                expect(waitCallback).to.have.been.calledWith("start");
            });
        it('should stop the indicator after all REST calls in the form load have ' +
            'completed', function() {
                var forks_field = {},
                    adhoc_verbosity_options = {};
                forks_field.default = "1";
                $scope.$apply(function() {
                    $scope.forks_field = forks_field;
                    $scope.adhoc_verbosity_options = adhoc_verbosity_options;
                });
                waitCallback.reset();
                $scope.$emit('adhocFormReady');
                $scope.$emit('adhocFormReady');
                expect(waitCallback).to.have.been.calledWith("stop");
            });
    });

    describe("instantiateArgumentHelp", function() {
        it("should initially provide a canned argument help response", function() {
            expect($scope.argsPopOver).to.equal('<p>These arguments are used ' +
                'with the specified module.</p>');
        });

        it("should change the help response when the module changes", function() {
            $scope.$apply(function () {
                $scope.module_name = {value: 'foo'};
            });
            expect($scope.argsPopOver).to.equal('<p>These arguments are used ' +
                'with the specified module. You can find information about ' +
                'the foo module <a ' +
                'id=\"adhoc_module_arguments_docs_link_for_module_foo\" ' +
                'href=\"http://docs.ansible.com/foo_module.html\" ' +
                'target=\"_blank\">here</a>.</p>');
        });

        it("should change the help response when the module changes again", function() {
            $scope.$apply(function () {
                $scope.module_name = {value: 'bar'};
            });
            expect($scope.argsPopOver).to.equal('<p>These arguments are used ' +
                'with the specified module. You can find information about ' +
                'the bar module <a ' +
                'id=\"adhoc_module_arguments_docs_link_for_module_bar\" ' +
                'href=\"http://docs.ansible.com/bar_module.html\" ' +
                'target=\"_blank\">here</a>.</p>');
        });

        it("should change the help response back to the canned response " +
            "when no module is selected", function() {
                $scope.$apply(function () {
                    $scope.module_name = null;
                });
                expect($scope.argsPopOver).to.equal('<p>These arguments are used ' +
                    'with the specified module.</p>');
        });
    });

    describe("instantiateHostPatterns", function() {
        it("should initialize the limit object based on the provided host " +
            "pattern", function() {
                ctrl.privateFn.instantiateHostPatterns("foo:bar");
                expect($scope.limit).to.equal("foo:bar");
            });

        it("should set the providedHostPatterns variable to the provided host " +
            "pattern so it is accesible on form reset", function() {
                ctrl.privateFn.instantiateHostPatterns("foo:bar");
                expect($scope.providedHostPatterns).to.equal("foo:bar");
            });

        it("should remove the hostPattern from rootScope after it has been " +
            "utilized", function() {
                $rootScope.hostPatterns = "foo";
                expect($rootScope.hostPatterns).to.exist;
                ctrl.privateFn.instantiateHostPatterns("foo");
                expect($rootScope.hostPatterns).to.not.exist;
            });
    });
    */
});
