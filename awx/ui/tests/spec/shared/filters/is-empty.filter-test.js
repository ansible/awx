'use strict';

describe('Filter: isEmpty', () => {
    var filter;

    beforeEach(angular.mock.module('awApp'));

    beforeEach(function(){
      inject(function($injector){
        filter = $injector.get('$filter')('isEmpty');
      });
    });

    it('check if an object is empty', function(){
      expect(filter({})).toBe(true);
      expect(filter({foo: 'bar'})).toBe(false);
    });
});
