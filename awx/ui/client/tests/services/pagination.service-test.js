import '../support/node';

import paginationModule from 'shared/pagination/main';

describe("pagination.service", function() {
    var $httpBackend, pagination;

    beforeEach("instantiate the pagination module", function() {
        angular.mock.module(paginationModule.name);
    });

    beforeEach("put the service and deps in scope", inject(function($injector) {
        $httpBackend = $injector.get('$httpBackend');
        pagination = $injector.get('pagination');
    }));

    afterEach(function() {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    describe("getInitialPageForList", function() {
        it('should return page given obj is on', function() {
            // get the name of the object
            $httpBackend.when('GET', '/url/?id=1')
                .respond({results: [{name: "foo"}]});
            // get how many results are less than or equal to
            // the name
            $httpBackend.when('GET', '/url/?name__lte=foo')
                .respond({count: 24});


            var page = pagination.getInitialPageForList("1", "/url/", 20);
            $httpBackend.flush();

            expect(page).to.eventually.equal(2);
        });
    });
});
