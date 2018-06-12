'use strict';

describe('Directive: Smart Search', () => {
    let $scope,
        $q,
        template,
        element,
        dom,
        $compile,
        $state = {},
        GetBasePath,
        QuerySet,
        ConfigService = {},
        i18n,
        $transitions,
        translateFilter;

    beforeEach(angular.mock.module('shared'));
    beforeEach(angular.mock.module('SmartSearchModule', ($provide) => {
        QuerySet = jasmine.createSpyObj('QuerySet', [
            'decodeParam',
            'search',
            'stripDefaultParams',
            'createSearchTagsFromQueryset',
            'initFieldset'
        ]);
        QuerySet.decodeParam.and.callFake((key, value) => {
            return `${key.split('__').join(':')}:${value}`;
        });
        QuerySet.stripDefaultParams.and.returnValue([]);
        QuerySet.createSearchTagsFromQueryset.and.returnValue([]);

        $transitions = jasmine.createSpyObj('$transitions', [
            'onSuccess'
        ]);
        $transitions.onSuccess.and.returnValue({});

        ConfigService = jasmine.createSpyObj('ConfigService', [
            'getConfig'
        ]);

        GetBasePath = jasmine.createSpy('GetBasePath');
        translateFilter = jasmine.createSpy('translateFilter');
        i18n = jasmine.createSpy('i18n');
        $state = jasmine.createSpyObj('$state', ['go']);
        $state.go.and.callFake(() => { return { then: function(){} }; });

        $provide.value('ConfigService', ConfigService);
        $provide.value('QuerySet', QuerySet);
        $provide.value('GetBasePath', GetBasePath);
        $provide.value('$state', $state);
        $provide.value('i18n', { '_': (a) => { return a; } });
        $provide.value('translateFilter', translateFilter);
    }));
    beforeEach(angular.mock.inject(($templateCache, _$rootScope_, _$compile_, _$q_) => {
        $q = _$q_;
        $compile = _$compile_;
        $scope = _$rootScope_.$new();

        ConfigService.getConfig.and.returnValue($q.when({}));
        QuerySet.search.and.returnValue($q.when({}));

        QuerySet.initFieldset.and.callFake(() => {
            var deferred = $q.defer();
            deferred.resolve({
                models: {
                    mock: {
                        base: {}
                    }
                },
                options: {
                    data: null
                }
            });
            return deferred.promise;
        });

        // populate $templateCache with directive.templateUrl at test runtime,
        template = window.__html__['client/src/shared/smart-search/smart-search.partial.html'];
        $templateCache.put('/static/partials/shared/smart-search/smart-search.partial.html', template);
    }));

    describe('clear all', () => {
        it('should revert search back to non-null defaults and remove page', () => {
            $state.$current = {
                path: {
                    mock: {
                        params: {
                            mock_search: {
                                config: {
                                    value: {
                                        page_size: '20',
                                        order_by: '-finished',
                                        page: '1',
                                        some_null_param: null
                                    }
                                }
                            }
                        }
                    }
                }
            };
            $state.params = {
                mock_search: {
                    page_size: '25',
                    order_by: 'name',
                    page: '11',
                    description_icontains: 'ansible',
                    name_icontains: 'ansible'
                }
            };
            $scope.list = {
                iterator: 'mock'
            };
            dom = angular.element(`<smart-search
                django-model="mock"
                search-size="mock"
                base-path="mock"
                iterator="mock"
                collection="dataset"
                search-tags="searchTags"
                list="list"
                >
                </smart-search>`);
            element = $compile(dom)($scope);
            $scope.$digest();
            const scope = element.isolateScope();
            scope.clearAllTerms();
            expect(QuerySet.search).toHaveBeenCalledWith('mock', {page_size: '20',order_by: '-finished',});
        });
    });
});
