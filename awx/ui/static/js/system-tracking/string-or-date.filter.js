/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    [   'amDateFormatFilter',
        'moment',
        function(dateFormat, moment) {
            return function(string, format) {
                if (moment.isMoment(string)) {
                    return dateFormat(string, format);
                } else {
                    return string;
                }
            };
        }
    ];
