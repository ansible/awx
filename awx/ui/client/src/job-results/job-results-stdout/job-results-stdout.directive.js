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
            var toDestroy = [],
                resizer,
                scrollWatcher;

            scope.$on('$destroy', function(){
                $(window).off("resize", resizer);
                $(window).off("scroll", scrollWatcher);
                $(".JobResultsStdOut-stdoutContainer").off('scroll',
                    scrollWatcher);
                toDestroy.forEach(closureFunc => closureFunc());
            });

            scope.stdoutContainerAvailable.resolve("container available");
            // utility function used to find the top visible line and
            // parent header in the pane
            //
            // note that while this function is called when in mobile width
            // the line anchor is not displayed in the css so calls
            // to lineAnchor do nothing
            var findTopLines = function() {
                var $container = $('.JobResultsStdOut-stdoutContainer');

                // get the first visible line's head element
                var getHeadElement = function (line) {
                    var lineHasHeaderClass = !!(line
                        .hasClass("header_play") ||
                            line.hasClass("header_task"));
                    var lineClassList;
                    var lineUUIDClass;

                    if (lineHasHeaderClass) {
                        // find head element when the first visible
                        // line is a header

                        lineClassList = line.attr("class")
                            .split(" ");

                        // get the header class w task uuid...
                        lineUUIDClass = lineClassList
                            .filter(n => n
                                .indexOf("header_task_") > -1)[0];

                        // ...if that doesn't exist get the one
                        // w play uuid
                        if (!lineUUIDClass) {
                            lineUUIDClass = lineClassList
                                .filter(n => n.
                                    indexOf("header_play_") > -1)[0];
                        }

                        // get the header line (not their might
                        // be more than one, so get the one with
                        // the actual header class)
                        //
                        // TODO it might be better in this case to just
                        // return `line` (less jumping with a cowsay
                        // case)
                        return $(".actual_header." +
                            lineUUIDClass);
                    } else {
                        // find head element when the first visible
                        // line is not a header

                        lineClassList = line.attr("class")
                            .split(" ");

                        // get the class w task uuid...
                        lineUUIDClass = lineClassList
                            .filter(n => n
                                .indexOf("task_") > -1)[0];

                        // ...if that doesn't exist get the one
                        // w play uuid
                        if (!lineUUIDClass) {
                            lineUUIDClass = lineClassList
                                .filter(n => n
                                    .indexOf("play_") > -1)[0];
                        }

                        // get the header line (not their might
                        // be more than one, so get the one with
                        // the actual header class)
                        return $(".actual_header.header_" +
                            lineUUIDClass);
                    }
                };

                var visItem,
                    parentItem;

                // iterate through each line of standard out
                $container.find('.JobResultsStdOut-aLineOfStdOut:visible')
                    .each( function () {
                        var $this = $(this);

                        // check to see if the line is the first visible
                        // line in the viewport...
                        if ($this.position().top >= 0) {

                            // ...if it is, return the line number
                            // for this line
                            visItem = parseInt($($this
                                .children()[0])
                                .text());

                            // as well as the line number for it's
                            // closest parent header line
                            var $head = getHeadElement($this);
                            parentItem = parseInt($($head
                                .children()[0])
                                .text());

                            // stop iterating over the standard out
                            // lines once the first one has been
                            // found

                            $this = null;
                            return false;
                        }

                        $this = null;
                    });

                $container = null;

                return {
                    visLine: visItem,
                    parentVisLine: parentItem
                };
            };

            // find if window is initially mobile or desktop width
            if (window.innerWidth <= 1200) {
                scope.isMobile = true;
            } else {
                scope.isMobile = false;
            }

            resizer = function() {
                // and update the isMobile var accordingly
                if (window.innerWidth <= 1200 && !scope.isMobile) {
                    scope.isMobile = true;
                } else if (window.innerWidth > 1200 & scope.isMobile) {
                    scope.isMobile = false;
                }
            };
            // watch changes to the window size
            $(window).resize(resizer);

            var lastScrollTop;

            var initScrollTop = function() {
                lastScrollTop = 0;
            };
            scrollWatcher = function() {
                var st = $(this).scrollTop();
                var netScroll = st + $(this).innerHeight();
                var fullHeight;

                if (st < lastScrollTop){
                    // user up scrolled, so disengage follow
                    scope.followEngaged = false;
                }

                if (scope.isMobile) {
                    // for mobile the height is the body of the entire
                    // page
                    fullHeight = $("body").height();
                } else {
                    // for desktop the height is the body of the
                    // stdoutContainer, minus the "^ TOP" indicator
                    fullHeight = $(this)[0].scrollHeight - 25;
                }

                if(netScroll >= fullHeight) {
                    // user scrolled all the way to bottom, so engage
                    // follow
                    scope.followEngaged = true;
                }

                // pane is now overflowed, show top indicator.
                if (st > 0) {
                    scope.stdoutOverflowed = true;
                }

                lastScrollTop = st;

                st = null;
                netScroll = null;
                fullHeight = null;
            };

            // update scroll watchers when isMobile changes based on
            // window resize
            toDestroy.push(scope.$watch('isMobile', function(val) {
                if (val === true) {
                    // make sure ^ TOP always shown for mobile
                    scope.stdoutOverflowed = true;

                    // unbind scroll watcher on standard out container
                    $(".JobResultsStdOut-stdoutContainer")
                        .unbind('scroll');

                    // init scroll watcher on window
                    initScrollTop();
                    $(window).on('scroll', scrollWatcher);

                } else if (val === false) {
                    // unbind scroll watcher on window
                    $(window).unbind('scroll');

                    // init scroll watcher on standard out container
                    initScrollTop();
                    $(".JobResultsStdOut-stdoutContainer").on('scroll',
                        scrollWatcher);
                }
            }));

            // called to scroll to follow anchor
            scope.followScroll = function() {
                // a double-check to make sure the follow anchor is at
                // the bottom of the standard out container
                $(".JobResultsStdOut-followAnchor")
                    .appendTo(".JobResultsStdOut-stdoutContainer");

                $location.hash('followAnchor');
                $anchorScroll();
            };

            // called to scroll to top of standard out (when "^ TOP" is
            // clicked)
            scope.toTop = function() {
                $location.hash('topAnchor');
                $anchorScroll();
            };

            // called to scroll to the current line anchor
            // when expand all/collapse all/filtering is engaged
            //
            // note that while this function can be called when in mobile
            // width the line anchor is not displayed in the css so those
            // calls do nothing
            scope.lineAnchor = function() {
                $location.hash('lineAnchor');
                $anchorScroll();
            };

            // if following becomes active, go ahead and get to the bottom
            // of the standard out pane
            toDestroy.push(scope.$watch('followEngaged', function(val) {
                // scroll to follow point if followEngaged is true
                if (val) {
                    scope.followScroll();
                }

                // set up tooltip changes for not finsihed job
                if (!scope.jobFinished) {
                    if (val) {
                        scope.followTooltip = "Currently following standard out as it comes in.  Click to unfollow.";
                    } else {
                        scope.followTooltip = "Click to follow standard out as it comes in.";
                    }
                }
            }));

            // follow button ng-click function
            scope.followToggleClicked = function() {
                if (scope.jobFinished) {
                    // when the job is finished engage followScroll
                    scope.followScroll();
                } else {
                    // when the job is not finished toggle followEngaged
                    // which is watched above
                    scope.followEngaged = !scope.followEngaged;
                }
            };

            // expand all/collapse all ng-click function
            scope.toggleAllStdout = function(type) {
                // find the top visible line in the container currently,
                // as well as the header parent of that line
                var topLines = findTopLines();

                if (type === 'expand') {
                    // for expand prepend the lineAnchor to the visible
                    // line
                    $(".line_num_" + topLines.visLine)
                        .prepend($("#lineAnchor"));
                } else {
                    // for collapse prepent the lineAnchor to the
                    // visible line's parent header
                    $(".line_num_" + topLines.parentVisLine)
                        .prepend($("#lineAnchor"));
                }

                var expandClass;
                if (type === 'expand') {
                    // for expand all, you'll need to find all the
                    // collapsed headers to expand them
                    expandClass = "fa-caret-right";
                } else {
                    // for collapse all, you'll need to find all the
                    // expanded headers to collapse them
                    expandClass = "fa-caret-down";
                }

                // find all applicable task headers that need to be
                // toggled
                element.find(".expanderizer--task."+expandClass)
                    .each((i, val) => {
                        // and trigger their expansion/collapsing
                        $timeout(function(){
                            // TODO change to a direct call of the
                            // toggleLine function
                            angular.element(val).trigger('click');
                            // TODO only call lineAnchor for those
                            // that are above the first visible line
                            scope.lineAnchor();
                        });
                    });

                // find all applicable play headers that need to be
                // toggled
                element.find(".expanderizer--play."+expandClass)
                    .each((i, val) => {
                        // for collapse all, only collapse play
                        // headers that do not have children task
                        // headers
                        if(angular.element("." +
                            angular.element(val).attr("data-uuid"))
                                .find(".expanderizer--task")
                                    .length === 0 ||
                                        type !== 'collapse') {

                                // trigger their expansion/
                                // collapsing
                                $timeout(function(){
                                    // TODO change to a direct
                                    // call of the
                                    // toggleLine function
                                    angular.element(val)
                                        .trigger('click');
                                    // TODO only call lineAnchor
                                    // for those that are above
                                    // the first visible line
                                    scope.lineAnchor();
                                });
                        }
                    });
            };

            // expand/collapse triangle ng-click function
            scope.toggleLine = function($event, id) {
                // if the section is currently expanded
                if ($($event.currentTarget).hasClass("fa-caret-down")) {
                    // hide all the children lines
                    $(id).hide();

                    // and change the triangle for the header to collapse
                    $($event.currentTarget)
                        .removeClass("fa-caret-down");
                    $($event.currentTarget)
                        .addClass("fa-caret-right");
                } else {
                    // if the section is currently collapsed

                    // show all the children lines
                    $(id).show();

                    // and change the triangle for the header to expanded
                    $($event.currentTarget)
                        .removeClass("fa-caret-right");
                    $($event.currentTarget)
                        .addClass("fa-caret-down");

                    // if the section you expanded is a play
                    if ($($event.currentTarget)
                        .hasClass("expanderizer--play")) {
                            // find all children task headers and
                            // expand them too
                            $("." + $($event.currentTarget)
                                .attr("data-uuid"))
                                .find(".expanderizer--task")
                                .each((i, val) => {
                                    if ($(val)
                                        .hasClass("fa-caret-right")) {
                                    $timeout(function(){
                                        // TODO change to a
                                        // direct call of the
                                        // toggleLine function
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
