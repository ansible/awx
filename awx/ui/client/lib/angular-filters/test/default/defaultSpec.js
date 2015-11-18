'use strict';

describe('default', function () {
  var defaultFilter;
  var numberFilter;

  beforeEach(module('frapontillo.ex.filters'));
  beforeEach(inject(function ($filter) {
    defaultFilter = $filter('default');
    numberFilter = $filter('number');
  }));

  it('should return the number 1337', function () {
    var inputVal = 1337;
    expect(defaultFilter(inputVal)).toEqual(1337);
  });

  it('should return a "default" string', function () {
    var inputVal;
    var defaultVal = 'default';
    expect(defaultFilter(inputVal, defaultVal)).toEqual('default');
  });

  it('should return a "default" string', function () {
    var inputVal = null;
    var defaultVal = 'default';
    expect(defaultFilter(inputVal, defaultVal)).toEqual('default');
  });

  it('should return a "default" string', function () {
    var inputVal = NaN;
    var defaultVal = 'default';
    expect(defaultFilter(inputVal, defaultVal)).toEqual('default');
  });

  it('should return the number 0', function () {
    var inputVal = 0;
    var defaultVal = 'default';
    expect(defaultFilter(inputVal, defaultVal)).toEqual(0);
  });

  it('should return the string "13.37"', function () {
    var inputVal = '13.3678787';
    var defaultVal = 'N.A.';
    expect(defaultFilter(numberFilter(inputVal, 2), defaultVal)).toEqual('13.37');
  });

  it('should return a "N.A." string', function () {
    var inputVal;
    var defaultVal = 'N.A.';
    expect(defaultFilter(numberFilter(inputVal, 2), defaultVal)).toEqual(defaultVal);
  });
});
