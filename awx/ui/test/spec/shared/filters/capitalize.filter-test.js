'use strict';

describe('Filter: capitalize', () => {
    var filter;

    beforeEach(angular.mock.module('awApp'));

    beforeEach(function(){
      inject(function($injector){
        filter = $injector.get('$filter')('capitalize');
      });
    });

    it('should capitalize the first letter', function(){
      expect(filter("foo")).toBe("Foo");
      expect(filter("Foo")).toBe("Foo");
      expect(filter("FOO")).toBe("Foo");
      expect(filter("FoO")).toBe("Foo");
    });
});
