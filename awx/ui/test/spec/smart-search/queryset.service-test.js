'use strict';

describe('Service: QuerySet', () => {
    let $httpBackend,
        QuerySet,
        Authorization,
        SmartSearchService;

    beforeEach(angular.mock.module('awApp', ($provide) =>{
        // @todo: improve app source / write testing utilities for interim
        // we don't want to be concerned with this provision in every test that involves the Rest module
        Authorization = {
            getToken: () => true,
            isUserLoggedIn: angular.noop
        };
        $provide.value('LoadBasePaths', angular.noop);
        $provide.value('Authorization', Authorization);
    }));
    beforeEach(angular.mock.module('RestServices'));

    beforeEach(angular.mock.inject((_$httpBackend_, _QuerySet_, _SmartSearchService_) => {
        $httpBackend = _$httpBackend_;
        QuerySet = _QuerySet_;
        SmartSearchService = _SmartSearchService_;

        // @todo: improve app source
        // config.js / local_settings emit $http requests in the app's run block
        $httpBackend
            .whenGET(/\/static\/*/)
            .respond(200, {});
        // @todo: improve appsource
        // provide api version via package.json config block
        $httpBackend
            .whenGET(/^\/api\/?$/)
            .respond(200, '');
    }));

    describe('fn encodeParam', () => {
        it('should encode parameters properly', () =>{
            expect(QuerySet.encodeParam({term: "name:foo", searchTerm: true})).toEqual({"name__icontains_DEFAULT" : "foo"});
            expect(QuerySet.encodeParam({term: "-name:foo", searchTerm: true})).toEqual({"not__name__icontains_DEFAULT" : "foo"});
            expect(QuerySet.encodeParam({term: "name:'foo bar'", searchTerm: true})).toEqual({"name__icontains_DEFAULT" : "'foo%20bar'"});
            expect(QuerySet.encodeParam({term: "-name:'foo bar'", searchTerm: true})).toEqual({"not__name__icontains_DEFAULT" : "'foo%20bar'"});
            expect(QuerySet.encodeParam({term: "organization:foo", relatedSearchTerm: true})).toEqual({"organization__search_DEFAULT" : "foo"});
            expect(QuerySet.encodeParam({term: "-organization:foo", relatedSearchTerm: true})).toEqual({"not__organization__search_DEFAULT" : "foo"});
            expect(QuerySet.encodeParam({term: "organization.name:foo", relatedSearchTerm: true})).toEqual({"organization__name" : "foo"});
            expect(QuerySet.encodeParam({term: "-organization.name:foo", relatedSearchTerm: true})).toEqual({"not__organization__name" : "foo"});
            expect(QuerySet.encodeParam({term: "id:11", searchTerm: true})).toEqual({"id__icontains_DEFAULT" : "11"});
            expect(QuerySet.encodeParam({term: "-id:11", searchTerm: true})).toEqual({"not__id__icontains_DEFAULT" : "11"});
            expect(QuerySet.encodeParam({term: "id:>11", searchTerm: true})).toEqual({"id__gt" : "11"});
            expect(QuerySet.encodeParam({term: "-id:>11", searchTerm: true})).toEqual({"not__id__gt" : "11"});
            expect(QuerySet.encodeParam({term: "id:>=11", searchTerm: true})).toEqual({"id__gte" : "11"});
            expect(QuerySet.encodeParam({term: "-id:>=11", searchTerm: true})).toEqual({"not__id__gte" : "11"});
            expect(QuerySet.encodeParam({term: "id:<11", searchTerm: true})).toEqual({"id__lt" : "11"});
            expect(QuerySet.encodeParam({term: "-id:<11", searchTerm: true})).toEqual({"not__id__lt" : "11"});
            expect(QuerySet.encodeParam({term: "id:<=11", searchTerm: true})).toEqual({"id__lte" : "11"});
            expect(QuerySet.encodeParam({term: "-id:<=11", searchTerm: true})).toEqual({"not__id__lte" : "11"});
        });
    });


    describe('fn search', () => {
        let pattern = /\/api\/v2\/inventories\/(.+)\/groups\/*/,
            endpoint = '/api/v2/inventories/1/groups/',
            params = {
            or__name: 'borg',
            or__description__icontains: 'assimilate'
        };

        it('should GET expected URL', () =>{
            $httpBackend
                .expectGET(pattern)
                .respond(200, {});
            QuerySet.search(endpoint, params).then((data) =>{
                expect(data.config.url).toEqual('/api/v2/inventories/1/groups/?or__name=borg&or__description__icontains=assimilate');
            });
            $httpBackend.flush();
        });

        xit('should memoize new DjangoModel', ()=>{});
        xit('should not replace memoized DjangoModel', ()=>{});
        xit('should provide an alias interface', ()=>{});

        afterEach(() => {
            $httpBackend.verifyNoOutstandingExpectation();
            $httpBackend.verifyNoOutstandingRequest();
        });
    });

});
