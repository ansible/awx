/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

function longDateFilter(moment, input) {
    var date = moment(input);
    return date.format('l LTS');
}

angular.module('longDateFilter', [])
    .filter('longDate',
            [   'moment',
                function(moment) {
                    return _.partial(longDateFilter, moment);
                }
            ]);
