describe('Job Status Graph Directive', function() {
  var element, scope, httpBackend;

  beforeEach(module('Tower'));

  beforeEach(module(function($provide) {
    $provide.value('LoadBasePaths', angular.noop);
  }));

  beforeEach(inject(function($rootScope, $compile, $httpBackend) {
    httpBackend = $httpBackend;
    $httpBackend.expectGET('/static/js/local_config.js').respond({
    });

    $httpBackend.whenGET('/static/partials/job_status_graph.html')
      .respond("<div class='m'></div><div class='n'></div><div class='job-status-graph'><svg></svg></div>");

    // $httpBackend.whenGET('/api/').respond(200,
    //                                       {"available_versions": {"v1": "/api/v1/"}, "description": "Ansible Tower REST API", "current_version": "/api/v1/"});

    scope = $rootScope.$new();

    element = '<div job-status-graph class="job-status-graph" data="data"></div>';

    // Takes jobs grouped by result (successful or failure
    //  Then looks at each array of arrays, where index 0 is the timestamp & index 1 is the count of jobs with that status
    scope.data =
      { jobs:
          { successful: [[1, 0], [2, 0], [3,0], [4,0], [5,0]],
            failed: [[1,0],[2,0],[3,0],[4,0],[5,0]]
          }
      };

    element = $compile(element)(scope);
    scope.$digest();

    $httpBackend.flush();

  }));

  afterEach(function() {
     httpBackend.verifyNoOutstandingExpectation();
     httpBackend.verifyNoOutstandingRequest();
  });

  function filterDataSeries(key, data) {
    return data.map(function(datum) {
      return datum.values;
    })[key];
  }

  it('uses successes & failures from scope', function() {
    var chartContainer = d3.select(element.find('svg')[0]);
    var lineData = chartContainer.datum();

    var successfulSeries = filterDataSeries(0, lineData);
    var failedSeries = filterDataSeries(1, lineData);

    expect(successfulSeries).to.eql(
    [ {x: 1, y: 0, series: 0},
      {x: 2, y: 0, series: 0},
      {x: 3, y: 0, series: 0},
      {x: 4, y: 0, series: 0},
      {x: 5, y: 0, series: 0}]);

    expect(failedSeries).to.eql(
      [ {x: 1, y: 0, series: 1},
        {x: 2, y: 0, series: 1},
        {x: 3, y: 0, series: 1},
        {x: 4, y: 0, series: 1},
        {x: 5, y: 0, series: 1}]);
  });

});

