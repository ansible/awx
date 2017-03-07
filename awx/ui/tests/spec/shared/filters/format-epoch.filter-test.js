'use strict';

describe('Filter: formatEpoch', () => {
    var filter;

    beforeEach(angular.mock.module('Tower'));

    beforeEach(function(){
      inject(function($injector){
        filter = $injector.get('$filter')('formatEpoch');
      });
    });

    it('should convert epoch to datetime string', function(){
      expect(filter(11111)).toBe("Dec 31, 1969 10:05 PM");
      expect(filter(610430400)).toBe("May 6, 1989 12:00 AM");
    });
});
