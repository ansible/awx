'use strict';

describe('lastNotNull', function () {
  var lastNotNullFilter;

  beforeEach(module('frapontillo.ex.filters'));
  beforeEach(inject(function ($filter) {
    lastNotNullFilter = $filter('lastNotNull');
  }));

  it('should return the number 0', function () {
    expect(lastNotNullFilter([
      null, undefined, 1337, 0
    ])).toEqual(0);
  });

  it('should return the number 1337', function () {
    expect(lastNotNullFilter([
      null, 0, 1337, undefined
    ])).toEqual(1337);
  });

  it('should return undefined', function () {
    expect(lastNotNullFilter([
      null, undefined
    ])).toEqual(undefined);
  });
});