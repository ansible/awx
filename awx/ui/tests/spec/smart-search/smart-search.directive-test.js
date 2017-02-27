'use strict';

xdescribe('Directive: Smart Search', () => {
    let $scope,
        template,
        element,
        dom,
        $compile,
        $state = {},
        $stateParams,
        GetBasePath,
        QuerySet;

    beforeEach(angular.mock.module('shared'));
    beforeEach(angular.mock.module('SmartSearchModule', ($provide) => {
        QuerySet = jasmine.createSpyObj('QuerySet', ['decodeParam']);
        QuerySet.decodeParam.and.callFake((key, value) => {
            return `${key.split('__').join(':')}:${value}`;
        });
        GetBasePath = jasmine.createSpy('GetBasePath');

        $provide.value('QuerySet', QuerySet);
        $provide.value('GetBasePath', GetBasePath);
        $provide.value('$state', $state);
    }));
    beforeEach(angular.mock.inject(($templateCache, _$rootScope_, _$compile_) => {
        // populate $templateCache with directive.templateUrl at test runtime,
        template = window.__html__['client/src/shared/smart-search/smart-search.partial.html'];
        $templateCache.put('/static/partials/shared/smart-search/smart-search.partial.html', template);

        $compile = _$compile_;
        $scope = _$rootScope_.$new();
    }));

    describe('initializing tags', () => {
        beforeEach(() => {
            QuerySet.initFieldset = function() {
                return {
                    then: function() {
                        return;
                    }
                };
            };
        });
        // some defaults like page_size and page will always be provided
        // but should be squashed if initialized with default values
        it('should not create tags', () => {
            $state.$current = {
                params: {
                    mock_search: {
                        config: {
                            value: {
                                page_size: '20',
                                order_by: '-finished',
                                page: '1'
                            }
                        }
                    }
                }
            };
            $state.params = {
                mock_search: {
                    page_size: '20',
                    order_by: '-finished',
                    page: '1'
                }
            };
            dom = angular.element(`<smart-search
                django-model="mock"
                search-size="mock"
                base-path="mock"
                iterator="mock"
                collection="dataset"
                search-tags="searchTags"
                >
                </smart-search>`);
            element = $compile(dom)($scope);
            $scope.$digest();
            expect($('.SmartSearch-tagContainer', element).length).toEqual(0);
        });
        // set one possible default (order_by) with a custom value, but not another default (page_size)
        it('should create an order_by tag, but not a page_size tag', () => {
            $state.$current = {
                params: {
                    mock_search: {
                        config: {
                            value: {
                                page_size: '20',
                                order_by: '-finished'
                            }
                        }
                    }
                }
            };
            $state.params = {
                mock_search: {
                    page_size: '20',
                    order_by: 'name'
                }
            };
            dom = angular.element(`<smart-search
                django-model="mock"
                search-size="mock"
                base-path="mock"
                iterator="mock"
                collection="dataset"
                search-tags="searchTags"
                >
                </smart-search>`);
            element = $compile(dom)($scope);
            $scope.$digest();
            expect($('.SmartSearch-tagContainer', element).length).toEqual(1);
            expect($('.SmartSearch-tagContainer .SmartSearch-name', element)[0].innerText).toEqual('order_by:name');
        });
        // set many possible defaults and many non-defaults - page_size and page shouldn't generate tags, even when non-default values are set
        it('should create an order_by tag, name tag, description tag - but not a page_size or page tag', () => {
            $state.$current = {
                params: {
                    mock_search: {
                        config: {
                            value: {
                                page_size: '20',
                                order_by: '-finished',
                                page: '1'
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
            dom = angular.element(`<smart-search
                django-model="mock"
                search-size="mock"
                base-path="mock"
                iterator="mock"
                collection="dataset"
                search-tags="searchTags"
                >
                </smart-search>`);
            element = $compile(dom)($scope);
            $scope.$digest();
            expect($('.SmartSearch-tagContainer', element).length).toEqual(3);
        });
    });

    describe('removing tags', () => {
        // assert a default value is still provided after a custom tag is removed
        xit('should revert to state-defined order_by when order_by tag is removed', () => {});
    });

    describe('accessing model', () => {
        xit('should retrieve cached model OPTIONS from localStorage', () => {});
        xit('should call QuerySet service to retrieve unstored model OPTIONS', () => {});
    });
});
