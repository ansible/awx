/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import datePicker from './date-picker.directive';

export default
    angular.module('systemTracking.datePicker',
                    [])
        .directive('datePicker', datePicker);
