'use strict';

describe('firstNotNull', function () {
  var firstNotNullFilter;

  beforeEach(module('frapontillo.ex.filters'));
  beforeEach(inject(function ($filter) {
    firstNotNullFilter = $filter('firstNotNull');
  }));

  it('should return the number 1337', function () {
    expect(firstNotNullFilter([
      null, undefined, 1337, 0
    ])).toEqual(1337);
  });

  it('should return the number 0', function () {
    expect(firstNotNullFilter([
      null, 0, undefined, 3
    ])).toEqual(0);
  });

  it('should return undefined', function () {
    expect(firstNotNullFilter([
      null, undefined
    ])).toEqual(undefined);
  });
});