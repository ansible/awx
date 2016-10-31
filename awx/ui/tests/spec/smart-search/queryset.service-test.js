'use strict';

describe('Service: QuerySet', () => {
    let $httpBackend,
        QuerySet,
        Authorization;

    beforeEach(angular.mock.module('Tower', ($provide) =>{
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

    beforeEach(angular.mock.inject((_$httpBackend_, _QuerySet_) => {
        $httpBackend = _$httpBackend_;
        QuerySet = _QuerySet_;

        // @todo: improve app source
        // config.js / local_settings emit $http requests in the app's run block
        $httpBackend
            .whenGET(/\/static\/*/)
            .respond(200, {});
        // @todo: improve appsource
        // provide api version via package.json config block
        $httpBackend
            .whenGET('/api/')
            .respond(200, '');
    }));

    describe('fn encodeQuery', () => {
        xit('null/undefined params should return an empty string', () => {
            expect(QuerySet.encodeQuery(null)).toEqual('');
            expect(QuerySet.encodeQuery(undefined)).toEqual('');
        });
        xit('should encode params to a string', () => {
            let params = {
                    or__created_by: 'Jenkins',
                    or__modified_by: 'Jenkins',
                    and__not__status: 'success',
                },
                result = '?or__created_by=Jenkins&or__modified_by=Jenkins&and__not__status=success';
            expect(QuerySet.encodeQuery(params)).toEqual(result);
        });
    });

    xdescribe('fn decodeQuery', () => {

    });


    describe('fn search', () => {
        let pattern = /\/api\/v1\/inventories\/(.+)\/groups\/*/,
            endpoint = '/api/v1/inventories/1/groups/',
            params = {
            or__name: 'borg',
            or__description__icontains: 'assimilate'
        };

        it('should GET expected URL', () =>{
            $httpBackend
                .expectGET(pattern)
                .respond(200, {});
            QuerySet.search(endpoint, params).then((data) =>{
                expect(data.config.url).toEqual('/api/v1/inventories/1/groups/?or__name=borg&or__description__icontains=assimilate');
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
