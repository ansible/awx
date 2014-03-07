'use strict';

describe('max', function () {
  var maxFilter;

  beforeEach(module('frapontillo.ex.filters'));
  beforeEach(inject(function ($filter) {
    maxFilter = $filter('max');
  }));

  it('should return the number 1337', function () {
    expect(maxFilter([
      null, undefined, 1337, 0
    ])).toEqual(1337);
  });

  it('should return the number 1337', function () {
    expect(maxFilter([
      null, 0, 1337, undefined
    ])).toEqual(1337);
  });

  it('should return undefined', function () {
    expect(maxFilter([
      null, undefined
    ])).toEqual(undefined);
  });
});