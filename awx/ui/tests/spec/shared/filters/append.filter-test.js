'use strict';

describe('Filter: append', () => {
    var filter;

    beforeEach(angular.mock.module('awApp'));

    beforeEach(function(){
      inject(function($injector){
        filter = $injector.get('$filter')('append');
      });
    });

    it('should append the two parameters passed', function(){
      expect(filter("foo", "bar")).toBe("foobar");
    });

    it('should return string if no append param passed', function(){
      expect(filter("foo")).toBe("foo");
    });

    it('should return empty string if no params passed', function(){
      expect(filter()).toBe("");
    });
});
