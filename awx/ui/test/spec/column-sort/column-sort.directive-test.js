'use strict';

xdescribe('Directive: column-sort', () =>{

    let $scope, template, $compile, QuerySet, GetBasePath;

    beforeEach(angular.mock.module('templateUrl'));
    beforeEach(function(){

        this.mock = {
            dataset: [
                {name: 'zero', idx: 0},
                {name: 'one', idx: 1},
                {name: 'two', idx: 2}
            ]
        };

        this.name_field = angular.element(`<column-sort
            collection="mock"
            dataset="mock.dataset"
            base-path="mock"
            column-iterator="mock"
            column-field="name"
            column-label="Name">
            </column-sort>`);

        this.idx_field = angular.element(`<column-sort
            collection="mock"
            dataset="mock.dataset"
            base-path="mock"
            column-iterator="mock"
            column-field="idx"
            column-label="Index">
            </column-sort>`);

        this.$state = {
            params: {},
            go: jasmine.createSpy('go')
        };

        this.$stateParams = {};

        var mockFilter = function (value) {
             return value;
        };

        angular.mock.module('ColumnSortModule', ($provide) =>{

            QuerySet = jasmine.createSpyObj('qs', ['search']);
            QuerySet.search.and.callFake(() => { return { then: function(){} }; });
            GetBasePath = jasmine.createSpy('GetBasePath');
            $provide.value('QuerySet', QuerySet);
            $provide.value('GetBasePath', GetBasePath);
            $provide.value('$state', this.$state);
            $provide.value('$stateParams', this.$stateParams);
            $provide.value("translateFilter", mockFilter);

        });
    });

    beforeEach(angular.mock.inject(($templateCache, _$rootScope_, _$compile_) => {
        template = window.__html__['client/src/shared/column-sort/column-sort.partial.html'];
        $templateCache.put('/static/partials/shared/column-sort/column-sort.partial.html', template);

        $compile = _$compile_;
        $scope = _$rootScope_.$new();
    }));

    it('should be ordered by name', function(){

        this.$state.params = {
            mock_search: {order_by: 'name'}
        };

        $compile(this.name_field)($scope);
        $compile(this.idx_field)($scope);

        $scope.$digest();
        expect( $(this.name_field).find('.columnSortIcon').hasClass('fa-sort-up') ).toEqual(true);
        expect( $(this.idx_field).find('.columnSortIcon').hasClass('fa-sort') ).toEqual(true);
    });

    it('should toggle to ascending name order, then ascending idx, then descending idx', function(){

        this.$state.params = {
            mock_search: {order_by: 'idx'}
        };

        $compile(this.name_field)($scope);
        $compile(this.idx_field)($scope);

        $scope.$digest();

        $(this.name_field).click();
        expect( $(this.name_field).find('.columnSortIcon').hasClass('fa-sort-up') ).toEqual(true);
        expect( $(this.idx_field).find('.columnSortIcon').hasClass('fa-sort') ).toEqual(true);

        $(this.idx_field).click();
        expect( $(this.name_field).find('.columnSortIcon').hasClass('fa-sort') ).toEqual(true);
        expect( $(this.idx_field).find('.columnSortIcon').hasClass('fa-sort-up') ).toEqual(true);

        $(this.idx_field).click();
        expect( $(this.name_field).find('.columnSortIcon').hasClass('fa-sort') ).toEqual(true);
        expect( $(this.idx_field).find('.columnSortIcon').hasClass('fa-sort-down') ).toEqual(true);
    });

});
