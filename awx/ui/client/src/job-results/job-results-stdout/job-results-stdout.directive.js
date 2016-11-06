/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

// import hostStatusBarController from './host-status-bar.controller';
export default [ 'templateUrl', '$timeout',
    function(templateUrl, $timeout) {
    return {
        scope: false,
        templateUrl: templateUrl('job-results/job-results-stdout/job-results-stdout'),
        restrict: 'E',
        link: function(scope, element, attrs) {
            scope.toggleAllStdout = function(type) {
                var expandClass;
                if (type === 'expand') {
                    expandClass = "fa-caret-right";
                } else {
                    expandClass = "fa-caret-down";
                }

                element.find(".expanderizer--task."+expandClass)
                    .each((i, val) => {
                        $timeout(function(){
                            angular.element(val).trigger('click');
                        });
                    });

                element.find(".expanderizer--play."+expandClass)
                    .each((i, val) => {
                        if(angular.element("." +
                            angular.element(val).attr("data-uuid"))
                                .find(".expanderizer--task")
                                    .length === 0 ||
                                        type !== 'collapse') {

                                $timeout(function(){
                                    angular.element(val)
                                        .trigger('click');
                                });
                        }
                    });
            };

            scope.toggleLine = function($event, id) {
                if ($($event.currentTarget).hasClass("fa-caret-down")) {
                    $(id).hide();
                    $($event.currentTarget)
                        .removeClass("fa-caret-down");
                    $($event.currentTarget)
                        .addClass("fa-caret-right");
                } else {
                    $(id).show();
                    $($event.currentTarget)
                        .removeClass("fa-caret-right");
                    $($event.currentTarget)
                        .addClass("fa-caret-down");

                    if ($($event.currentTarget)
                        .hasClass("expanderizer--play")) {
                            $("." + $($event.currentTarget)
                                .attr("data-uuid"))
                                .find(".expanderizer--task")
                                .each((i, val) => {
                                    if ($(val)
                                        .hasClass("fa-caret-right")) {
                                    $timeout(function(){
                                        angular.element(val)
                                            .trigger('click');
                                    });
                                }
                            });
                    }
                }
            };
        }
    };
}];
