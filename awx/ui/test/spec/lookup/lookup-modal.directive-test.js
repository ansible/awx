'use strict';

xdescribe('Directive: lookupModal', () => {

    let dom, element, listHtml, listDefinition, Dataset,
        lookupTemplate, paginateTemplate, searchTemplate, columnSortTemplate,
        $scope, $parent, $compile, $state;

    // mock dependency chains
    // (shared requires RestServices requires Authorization etc)
    beforeEach(angular.mock.module('login'));
    beforeEach(angular.mock.module('shared'));

    beforeEach(angular.mock.module('LookupModalModule', ($provide) => {
        $provide.value('smartSearch', angular.noop);
        $provide.value('columnSort', angular.noop);
        $provide.value('paginate', angular.noop);
        $state = jasmine.createSpyObj('$state', ['go']);
    }));

    beforeEach(angular.mock.inject(($templateCache, _$rootScope_, _$compile_, _generateList_) => {
        listDefinition = {
            name: 'mocks',
            iterator: 'mock',
            fields: {
                name: {}
            }
        };

        listHtml = _generateList_.build({
            mode: 'lookup',
            list: listDefinition,
            input_type: 'radio'
        });

        Dataset = {
            data: {
                results: [
                    { id: 1, name: 'Mock Resource 1' },
                    { id: 2, name: 'Mock Resource 2' },
                    { id: 3, name: 'Mock Resource 3' },
                    { id: 4, name: 'Mock Resource 4' },
                    { id: 5, name: 'Mock Resource 5' },
                ]
            }
        };

        dom = angular.element(`<lookup-modal>${listHtml}</lookup-modal>`);

        // populate $templateCache with directive.templateUrl at test runtime,
        lookupTemplate = window.__html__['client/src/shared/lookup/lookup-modal.partial.html'];
        paginateTemplate = window.__html__['client/src/shared/paginate/paginate.partial.html'];
        searchTemplate = window.__html__['client/src/shared/smart-search/smart-search.partial.html'];
        columnSortTemplate = window.__html__['client/src/shared/column-sort/column-sort.partial.html'];

        $templateCache.put('/static/partials/shared/lookup/lookup-modal.partial.html', lookupTemplate);
        $templateCache.put('/static/partials/shared/paginate/paginate.partial.html', paginateTemplate);
        $templateCache.put('/static/partials/shared/smart-search/smart-search.partial.html', searchTemplate);
        $templateCache.put('/static/partials/shared/column-sort/column-sort.partial.html', columnSortTemplate);

        $compile = _$compile_;
        $parent = _$rootScope_.$new();

        // mock resolvables
        $scope = $parent.$new();
        $scope.$resolve = {
            ListDefinition: listDefinition,
            Dataset: Dataset
        };
    }));

    it('Resource is pre-selected in form - corresponding radio should initialize checked', () => {
        $parent.mock = 1; // resource id
        $parent.mock_name = 'Mock Resource 1'; // resource name

        element = $compile(dom)($scope);
        $scope.$digest();

        expect($(':radio')[0].is(':checked')).toEqual(true);
    });

    it('No resource pre-selected in form - no radio should initialize checked', () => {
        element = $compile(dom)($scope);
        $scope.$digest();

        _.forEach($(':radio'), (radio) => {
            expect(radio.is('checked')).toEqual(false);
        });
    });

    it('Should update $parent / form scope and exit $state on save', () => {
        element = $compile(dom)($scope);
        $scope.$digest();
        $(':radio')[1].click();
        $('.Lookup-save')[0].click();

        expect($parent.mock).toEqual(2);
        expect($parent.mock_name).toEqual('Mock Resource 2');
        expect($state.go).toHaveBeenCalled();
    });

    it('Should not update $parent / form scope on exit via header', () => {
        $parent.mock = 3; // resource id
        $parent.mock_name = 'Mock Resource 3'; // resource name
        element = $compile(dom)($scope);
        $scope.$digest();

        $(':radio')[1].click();
        $('.Form-exit')[0].click();

        expect($parent.mock).toEqual(3);
        expect($parent.mock_name).toEqual('Mock Resource 3');
        expect($state.go).toHaveBeenCalled();
    });

    it('Should not update $parent / form scope on exit via cancel button', () => {
        $parent.mock = 3; // resource id
        $parent.mock_name = 'Mock Resource 3'; // resource name
        element = $compile(dom)($scope);
        $scope.$digest();

        $(':radio')[1].click();
        $('.Lookup-cancel')[0].click();

        expect($parent.mock).toEqual(3);
        expect($parent.mock_name).toEqual('Mock Resource 3');
        expect($state.go).toHaveBeenCalled();
    });
});
