'use strict';

describe('bool', function () {
  var boolFilter;

  beforeEach(module('frapontillo.ex.filters'));
  beforeEach(inject(function ($filter) {
    boolFilter = $filter('bool');
  }));

  it('should match the true value', function () {
    expect(boolFilter(true, 1, 0)).toEqual(1);
  });

  it('should match the false value', function () {
    expect(boolFilter(false, 1, 0)).toEqual(0);
  });

  it('should match a string to the false value', function () {
    expect(boolFilter('true', 1, 0)).toEqual(0);
  });

  it('should match the empty string to the false value', function () {
    expect(boolFilter('', 1, 0)).toEqual(0);
  });

  it('should match undefined to the false value', function () {
    expect(boolFilter(undefined, 1, 0)).toEqual(0);
  });

  it('should match null to the false value', function () {
    expect(boolFilter(null, 1, 0)).toEqual(0);
  });
});