'use strict';

describe('min', function () {
  var minFilter;

  beforeEach(module('frapontillo.ex.filters'));
  beforeEach(inject(function ($filter) {
    minFilter = $filter('min');
  }));

  it('should return the number 0', function () {
    expect(minFilter([
      null, undefined, 1337, 0
    ])).toEqual(0);
  });

  it('should return the number 1', function () {
    expect(minFilter([
      null, 1, 1337, undefined
    ])).toEqual(1);
  });

  it('should return undefined', function () {
    expect(minFilter([
      null, undefined
    ])).toEqual(undefined);
  });
});