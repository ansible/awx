'use strict';

describe('Filter: formatEpoch', () => {
    var filter;

    beforeEach(angular.mock.module('awApp'));

    beforeEach(function(){
      inject(function($injector){
        filter = $injector.get('$filter')('formatEpoch');
      });
    });

    // TODO: this test is opinionated - it assumes that the
    // system date on the machine that's running it is EST.
    // I'm not quite sure how to foce a moment to use a specific
    // timezone.  If we can figure that out then we can re-enable
    // these tests.

    xit('should convert epoch to datetime string', function(){
      expect(filter(11111)).toBe("Dec 31, 1969 10:05 PM");
      expect(filter(610430400)).toBe("May 6, 1989 12:00 AM");
    });
});
