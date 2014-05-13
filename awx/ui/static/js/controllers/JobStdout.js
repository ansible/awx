/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobStdout.js
 *
 */

'use strict';

function JobStdoutController ($scope, $compile, $routeParams, ClearScope, GetBasePath, Wait, Rest, ProcessErrors) {

    ClearScope();

    var job_id = $routeParams.id;

    Wait('start');

    if ($scope.removeLoadStdout) {
        $scope.removeLoadStdout();
    }
    $scope.removeLoadStdout = $scope.$on('LoadStdout', function(e, url) {
        Rest.setUrl(url + '?format=html');
        Rest.get()
            .success(function(data) {
                Wait('stop');
                $('#stdout-container').empty().html(data);
            })
            .error(function(data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                    msg: 'Failed to retrieve stdout for job: ' + job_id + '. GET returned: ' + status });
            });
    });
    
    Rest.setUrl(GetBasePath('jobs') + job_id + '/');
    Rest.get()
        .success(function(data) {
            $scope.job = data;
            $scope.$emit('LoadStdout', data.related.stdout);
        })
        .error(function(data, status) {
            ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                msg: 'Failed to retrieve job: ' + job_id + '. GET returned: ' + status });
        });
}

JobStdoutController.$inject = [ '$scope', '$compile', '$routeParams', 'ClearScope', 'GetBasePath', 'Wait', 'Rest', 'ProcessErrors'];