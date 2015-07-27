'use strict';

describe('property', function () {
  var propertyFilter;

  var testArray = [
    {id:0, text:'zero'},
    {id:1, text:'one'},
    {id:2, text:'two'},
    {id:3, text:'three'},
    {id:4, text:'four'},
    {id:5, text:'five'},
    {id:6, text:'six'}
  ];

  var makeArray = function() {
    return angular.copy(testArray);
  };

  beforeEach(module('frapontillo.ex.filters'));
  beforeEach(inject(function ($filter) {
    propertyFilter = $filter('property');
  }));

  it('should return the \'id\' properties', function () {
    var filteredArray = propertyFilter(makeArray(), 'id');
    expect(filteredArray[0]).toEqual(0);
    expect(filteredArray.length).toEqual(7);
  });

  it('should return elements with only the \'text\' property', function () {
    var filteredArray = propertyFilter(makeArray(), 'text');
    expect(filteredArray[0]).toEqual('zero');
    expect(filteredArray.length).toEqual(7);
  });

  it('should return empty elements', function () {
    var filteredArray = propertyFilter(makeArray(), 'something else');
    expect(filteredArray[0]).toEqual(undefined);
    expect(filteredArray.length).toEqual(7);
  });
});