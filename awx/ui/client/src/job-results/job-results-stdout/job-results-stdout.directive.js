/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

// import hostStatusBarController from './host-status-bar.controller';
export default [ 'templateUrl', '$timeout', '$location', '$anchorScroll',
    function(templateUrl, $timeout, $location, $anchorScroll) {
    return {
        scope: false,
        templateUrl: templateUrl('job-results/job-results-stdout/job-results-stdout'),
        restrict: 'E',
        link: function(scope, element) {

            var findTopLines = function() {
                scope.visibleItems = "";
                var $container = $('.JobResultsStdOut-stdoutContainer');
                var visItem,
                    parentItem;
                $container.find('.JobResultsStdOut-aLineOfStdOut').each( function () {
                    var $this = $(this);
                    if ( $this.position().top + $this.height() > $container.position().top &&
                        $this.position().top < ($container.height() + $container.position().top) ) {
                        visItem = parseInt($($this.children()[0]).text());

                        var $head,
                            classList,
                            header;
                        if ($this.hasClass("header_play") || $this.hasClass("header_task")) {
                            classList = $this.attr("class")
                                .split(" ");
                            header = classList
                                .filter(n => n.indexOf("header_task_") > -1)[0];
                            if (!header) {
                                header = classList
                                    .filter(n => n.indexOf("header_play_") > -1)[0];
                            }
                            $head = $(".actual_header." + header);
                        } else {
                            classList = $this.attr("class")
                                .split(" ");
                            header = classList
                                .filter(n => n.indexOf("task_") > -1)[0];
                            if (!header) {
                                header = classList
                                    .filter(n => n.indexOf("play_") > -1)[0];
                            }

                            $head = $(".actual_header.header_" + header);
                        }
                        parentItem = parseInt($($head.children()[0]).text());
                        return false;
                    }
                });
                scope.visLine = visItem;
                scope.parentVisLine = parentItem;
            };

            // find when window changes from mobile to desktop width
            if (window.innerWidth < 1200) {
                scope.isMobile = true;
            } else {
                scope.isMobile = false;
            }
            $( window ).resize(function() {
                if (window.innerWidth < 1200 && !scope.isMobile) {
                    scope.isMobile = true;
                } else if (window.innerWidth >= 1200 & scope.isMobile) {
                    scope.isMobile = false;
                }
            });

            var lastScrollTop;

            var initScrollTop = function() {
                lastScrollTop = 0;
            }
            var scrollWatcher = function() {
                var st = $(this).scrollTop(),
                    fullHeight;
                if (st < lastScrollTop){
                    // user up scrolled, so disengage follow
                    scope.followEngaged = false;
                }

                if (scope.isMobile) {
                    fullHeight = $("body").height();
                } else {
                    fullHeight = $(this)[0].scrollHeight - 25;
                }

                if($(this).scrollTop() + $(this).innerHeight() >=
                    fullHeight) {
                    // user scrolled all the way to bottom, so engage
                    // follow
                    scope.followEngaged = true;
                }

                // pane is now overflowed, show top indicator
                if (st > 0 && !scope.isMobile) {
                    scope.stdoutOverflowed = true;
                }

                lastScrollTop = st;
            }

            scope.$watch('isMobile', function(val) {
                if (val === true) {
                    // make sure ^ TOP always shown
                    scope.stdoutOverflowed = true;

                    initScrollTop();
                    $(".JobResultsStdOut-stdoutContainer")
                        .unbind('scroll');
                    $(window).on('scroll', scrollWatcher);

                } else if (val === false) {
                    initScrollTop();
                    $(window).unbind('scroll');
                    $(".JobResultsStdOut-stdoutContainer").on('scroll',
                        scrollWatcher);
                }
            });

            scope.followScroll = function() {
                $(".JobResultsStdOut-followAnchor")
                    .appendTo(".JobResultsStdOut-stdoutContainer");

                $location.hash('followAnchor');
                $anchorScroll();
            };

            scope.toTop = function() {
                $location.hash('topAnchor');
                $anchorScroll();
            };

            scope.lineAnchor = function() {
                $location.hash('lineAnchor');
                $anchorScroll();
            };

            // if following becomes active, go ahead and get to the bottom
            // of the standard out pane
            scope.$watch('followEngaged', function(val) {
                if (val) {
                    scope.followScroll();
                }

                if (!scope.jobFinished) {
                    if (val) {
                        scope.followTooltip = "Currently following standard out as it comes in.  Click to unfollow.";
                    } else {
                        scope.followTooltip = "Click to follow standard out as it comes in.";
                    }
                }
            });

            scope.followToggleClicked = function() {
                if (scope.jobFinished) {
                    scope.followScroll();
                } else {
                    scope.followEngaged = !scope.followEngaged;
                }
            };

            scope.toggleAllStdout = function(type) {
                findTopLines();

                if (type === 'expand') {
                    $(".line_num_" + scope.visLine)
                        .prepend($("#lineAnchor"));
                } else {
                    $(".line_num_" + scope.parentVisLine)
                        .prepend($("#lineAnchor"));
                }

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
                            scope.lineAnchor();
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
                                    scope.lineAnchor();
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
