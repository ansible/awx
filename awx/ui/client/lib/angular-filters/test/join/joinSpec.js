'use strict';

describe('join', function () {
  var joinFilter;

  beforeEach(module('frapontillo.ex.filters'));
  beforeEach(inject(function ($filter) {
    joinFilter = $filter('join');
  }));

  it('should return \'this is a simple test\'', function () {
    expect(joinFilter(['this', 'is', 'a', 'simple', 'test'], ' ')).toEqual('this is a simple test');
  });

  it('should return the empty string for an undefined array', function () {
    expect(joinFilter(undefined, '')).toEqual('');
  });

  it('should return the empty string for an empty array', function () {
    expect(joinFilter([], '')).toEqual('');
  });

  it('should return \'0123456789\'', function () {
    expect(joinFilter([0,1,2,3,4,5,6,7,8,9], '')).toEqual('0123456789');
  });

  it('should default to the comma separator and return \'0,1,2,3,4,5,6,7,8,9\'', function () {
    expect(joinFilter([0,1,2,3,4,5,6,7,8,9])).toEqual('0,1,2,3,4,5,6,7,8,9');
  });
});