'use strict';

describe('Filter: sanitize', () => {
    var filter;

    beforeEach(angular.mock.module('awApp'));

    beforeEach(function(){
      inject(function($injector){
        filter = $injector.get('$filter')('sanitize');
      });
    });

    it('should sanitize xss-vulnerable strings', function(){
      expect(filter("<div>foobar</div>")).toBe("&lt;div&gt;foobar&lt;/div&gt;");
    });
});
