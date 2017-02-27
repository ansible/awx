'use strict';

xdescribe('Directive: Paginate', () => {
    var dom = angular.element('<paginate base-path="mock" dataset="mock_dataset" iterator="mock"></paginate>'),
        template,
        element,
        $scope,
        $compile,
        $state,
        $stateParams = {};

    beforeEach(angular.mock.module('shared'), ($provide) =>{
        $provide.value('Rest', angular.noop);
    });
    beforeEach(angular.mock.module('PaginateModule', ($provide) => {
        $state = jasmine.createSpyObj('$state', ['go']);

        $provide.value('$stateParams', $stateParams);
        $provide.value('Rest', angular.noop);
    }));
    beforeEach(angular.mock.inject(($templateCache, _$rootScope_, _$compile_) => {
        // populate $templateCache with directive.templateUrl at test runtime,
        template = window.__html__['client/src/shared/paginate/paginate.partial.html'];
        $templateCache.put('/static/partials/shared/paginate/paginate.partial.html', template);

        $compile = _$compile_;
        $scope = _$rootScope_.$new();
    }));

    it('should be hidden if only 1 page of data', () => {

        $scope.mock_dataset = {count: 19};
        $scope.pageSize = 20;
        element = $compile(dom)($scope);
        $scope.$digest();

        expect($('.Paginate-wrapper', element)).hasClass('ng-hide');
    });
    describe('it should show expected page range', () => {


        it('should show 7 pages', () =>{

            $scope.pageSize = 1;
            $scope.mock_dataset = {count: 7};
            element = $compile(dom)($scope);
            $scope.$digest();
            // next, previous, 7 pages
            expect($('.Paginate-controls--item', element)).length.toEqual(9);
        });
        it('should show 100 pages', () =>{
            $scope.pageSize = 1;
            $scope.mock_dataset = {count: 100};
            element = $compile(dom)($scope);
            $scope.$digest();
            // first, next, previous, last, 100 pages
            expect($('.Paginate-controls--item', element)).length.toEqual(104);
        });
    });
    describe('it should get expected page', () => {

        it('should get the next page', () =>{

        $scope.mock_dataset = {
            count: 42,
        };

        $stateParams.mock_search = {
            page_size: 5,
            page: 1
        };

        element = $compile(dom)($scope);
        $('.Paginate-controls--next').click();
        expect($stateParams.mock_search.page).toEqual(2);
        });

        it('should get the previous page', ()=>{

            $scope.mock_dataset = {
                count: 42
            };
            $stateParams.mock_search = {
                page_size: 10,
                page: 3
            };

            element = $compile(dom)($scope);
            $('.Paginate-controls--previous');
            expect($stateParams.mock_search.page).toEqual(2);
        });
        it('should get the last page', ()=>{
            $scope.mock_dataset = {
                count: 110
            };
            $stateParams.mock_search = {
                page_size: 5,
                page: 1
            };
            $('.Paginate-controls--last').click();
            expect($stateParams.mock_search.page).toEqual(42);
        });
        it('should get the first page', () => {
            $scope.mock_dataset = {
                count: 110
            };
            $stateParams.mock_search = {
                page_size: 5,
                page: 35
            };
            $('.Paginate-controls--first').click();
            expect($stateParams.mock_search.page).toEqual(1);
        });

    });
});
