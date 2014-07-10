(function (ng) {
    'use strict';
    var module = ng.module('lrInfiniteScroll', []);

    module.directive('lrInfiniteScroll', ['$log', '$timeout', function ($log, timeout) {
        return{
            link: function (scope, element, attr) {
                var
                    lengthThreshold = attr.scrollThreshold || 50,
                    timeThreshold = attr.timeThreshold || 400,
                    direction = attr.direction || 'down',
                    handler = scope.$eval(attr.lrInfiniteScroll),
                    promise = null,
                    lastRemaining = 9999;

                lengthThreshold = parseInt(lengthThreshold, 10);
                timeThreshold = parseInt(timeThreshold, 10);

                if (!handler || !ng.isFunction(handler)) {
                    handler = ng.noop;
                }

                $log.debug('lrInfiniteScroll: ' + attr.lrInfiniteScroll);

                element.bind('scroll', function () {
                    var remaining = (direction === 'down') ? element[0].scrollHeight - (element[0].clientHeight + element[0].scrollTop) : element[0].scrollTop;
                    // if we have reached the threshold and we scroll down
                    if ((direction === 'down' && remaining < lengthThreshold && (remaining - lastRemaining) < 0) ||
                         direction === 'up' && remaining < lengthThreshold) {
                        //if there is already a timer running which has not expired yet we have to cancel it and restart the timer
                        if (promise !== null) {
                            timeout.cancel(promise);
                        }
                        promise = timeout(function () {
                            handler();
                            promise = null;
                        }, timeThreshold);
                    }
                    lastRemaining = remaining;
                });
            }

        };
    }]);
})(angular);
