/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export function searchDateRange(date) {
    return {
        from: moment(date).startOf('day'),
        to: moment(date).endOf('day')
    };
}
