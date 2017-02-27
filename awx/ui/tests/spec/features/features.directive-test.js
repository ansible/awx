'use strict';

describe('Directive: Features enabled/disabled', () => {
 let $compile,
      $scope,
      q;

  beforeEach(angular.mock.module('features'));

  beforeEach(angular.mock.inject((_$compile_, _$rootScope_, $q) => {
      $compile = _$compile_;
      $scope = _$rootScope_;
      q = $q;

      $scope.featuresConfigured = q.defer();
  }));

  it('Removes the element if feature is disabled', () => {
    let element = $compile("<div aw-feature='system-tracking'></div")($scope);
    $scope.$digest();
    expect(element.html()).toBe('');
  });
});
