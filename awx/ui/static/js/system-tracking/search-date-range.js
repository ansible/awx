/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import moment from 'tower/shared/moment/moment';

export function searchDateRange(dateString) {
    var date;

    switch(dateString) {
        case 'yesterday':
            date = moment().subtract(1, 'day');
            break;
        case 'tomorrow':
            date = moment().add(1, 'day');
            break;
        default:
            date = moment(dateString);
    }


    return {
        from: date.clone().startOf('day'),
        to: date.clone().add(1, 'day').startOf('day')
    };
}
