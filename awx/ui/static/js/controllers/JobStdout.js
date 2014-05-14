/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  JobStdout.js
 *
 */

'use strict';

function JobStdoutController ($scope, $compile, $routeParams, ClearScope, GetBasePath, Wait, Rest, ProcessErrors) {

    ClearScope();

    var available_height, job_id = $routeParams.id;

    Wait('start');

    if ($scope.removeLoadStdout) {
        $scope.removeLoadStdout();
    }
    $scope.removeLoadStdout = $scope.$on('LoadStdout', function(e, url) {
        Rest.setUrl(url + '?format=html');
        Rest.get()
            .success(function(data) {
                Wait('stop');
                $('#stdout-iframe').attr('srcdoc', data);
            })
            .error(function(data, status) {
                ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                    msg: 'Failed to retrieve stdout for job: ' + job_id + '. GET returned: ' + status });
            });
    });

    function resizeToFit() {
        available_height = $(window).height() - $('.main-menu').outerHeight() - $('#main_tabs').outerHeight() -
            $('#breadcrumb-container').outerHeight() - $('.site-footer').outerHeight();
        if ($(window).width() < 768) {
            available_height += 55;
        }
        else {
            available_height += 5;
        }
        $('#stdout-iframe').height(available_height);
        //$('#stdout-container').mCustomScrollbar("update");
    }
    resizeToFit();

    $(window).resize(_.debounce(function() {
        resizeToFit();
    }, 500));

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

JobStdoutController.$inject = [ '$scope', '$compile', '$routeParams', 'ClearScope', 'GetBasePath', 'Wait', 'Rest', 'ProcessErrors' ];