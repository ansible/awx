'use strict';

describe('Filter: longDate', () => {
    var filter;

    beforeEach(angular.mock.module('awApp'));

    beforeEach(function(){
      inject(function($injector){
        filter = $injector.get('$filter')('longDate');
      });
    });

    // TODO: this test is opinionated - it assumes that the
    // system date on the machine that's running it is EST.
    // I'm not quite sure how to foce a moment to use a specific
    // timezone.  If we can figure that out then we can re-enable
    // these tests.

    xit('should convert the timestamp to a UI friendly date and time', function(){
      expect(filter("2017-02-13T22:00:14.106Z")).toBe("2/13/2017 5:00:14 PM");
    });
    it('should return an empty string if no timestamp is passed', function(){
        expect(filter()).toBe("");
    });
});
