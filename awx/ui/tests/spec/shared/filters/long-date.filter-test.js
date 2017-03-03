'use strict';

describe('Filter: longDate', () => {
    var filter;

    beforeEach(angular.mock.module('Tower'));

    beforeEach(function(){
      inject(function($injector){
        filter = $injector.get('$filter')('longDate');
      });
    });

    it('should convert the timestamp to a UI friendly date and time', function(){
      expect(filter("2017-02-13T22:00:14.106Z")).toBe("2/13/2017 5:00:14 PM");
    });
    it('should return an empty string if no timestamp is passed', function(){
        expect(filter()).toBe("");
    });
});
