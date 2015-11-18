/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 
 /**
 * @ngdoc function
 * @name forms.function:JobEventData
 * @description Not sure if this is used...
*/

export default
    angular.module('JobEventDataDefinition', [])
        .value('JobEventDataForm', {

            editTitle: '{{ id }} - {{ event_display }}',
            name: 'job_events',
            well: false,
            'class': 'horizontal-narrow',

            fields: {
                event_data: {
                    label: false,
                    type: 'textarea',
                    readonly: true,
                    rows: 18,
                    'class': 'modal-input-xxlarge'
                }
            }

        }); //Form
