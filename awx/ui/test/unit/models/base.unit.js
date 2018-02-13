describe('Models | BaseModel', () => {
    let baseModel;

    beforeEach(() => {
        angular.mock.module('at.lib.services');
        angular.mock.module('at.lib.models');
    });

    beforeEach(angular.mock.inject(($injector) => {
        baseModel = new ($injector.get('BaseModel'))('test');
    }));

    describe('parseRequestConfig', () => {
        it('always returns the expected configuration', () => {
            const { parseRequestConfig } = baseModel;
            const data = { name: 'foo' };

            expect(parseRequestConfig('get')).toEqual({ method: 'get', resource: undefined });
            expect(parseRequestConfig('get', 1)).toEqual({ method: 'get', resource: 1 });
            expect(parseRequestConfig('post', { data })).toEqual({ method: 'post', data });
            expect(parseRequestConfig(['get', 'post'], [1, 2], { data }))
                .toEqual({ resource: [1, 2], method: ['get', 'post'] });
        });
    });
});
