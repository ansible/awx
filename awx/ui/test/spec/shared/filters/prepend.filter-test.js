'use strict';

describe('Filter: prepend', () => {
    var filter;

    beforeEach(angular.mock.module('awApp'));

    beforeEach(function(){
      inject(function($injector){
        filter = $injector.get('$filter')('prepend');
      });
    });

    it('should prepend the second param to the first', function(){
      expect(filter("foo", "bar")).toBe("barfoo");
    });

    it('should return string if no prepend param passed', function(){
      expect(filter("foo")).toBe("foo");
    });

    it('should return empty string if no params passed', function(){
      expect(filter()).toBe("");
    });
});
