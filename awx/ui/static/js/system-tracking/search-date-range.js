/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

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
        from: date.startOf('day'),
        to: date.endOf('day')
    };
}
