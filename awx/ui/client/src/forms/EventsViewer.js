/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 
 /**
 * @ngdoc function
 * @name forms.function:EventsViewer
 * @description This form is for events on the job detail page
*/

export default
    angular.module('EventsViewerFormDefinition', [])
        .factory('EventsViewerForm', ['i18n', function(i18n) {
        return {

            fields: {
                host_name: {
                    label: i18n._('Host'),
                    section: i18n._('Event')
                },
                status: {
                    labellabel: i18n._('Status'),
                    section: i18n._('Event')
                },
                id: {
                    labellabel: i18n._('ID'),
                    section: i18n._('Event')
                },
                created: {
                    labellabel: i18n._('Created On'),
                    section: i18n._('Event')
                },
                role: {
                    labellabel: i18n._('Role'),
                    section: i18n._('Event')
                },
                play: {
                    labellabel: i18n._('Play'),
                    type: 'text',
                    section: i18n._('Event')
                },
                task: {
                    labellabel: i18n._('Task'),
                    section: i18n._('Event')
                },
                item: {
                    labellabel: i18n._('Item'),
                    section: i18n._('Event')
                },
                module_name: {
                    labellabel: i18n._('Module'),
                    section: i18n._('Event')
                },
                module_args: {
                    labellabel: i18n._('Arguments'),
                    section: i18n._('Event')
                },
                rc: {
                    labellabel: i18n._('Return Code'),
                    section: i18n._('Results')
                },
                msg: {
                    labellabel: i18n._('Message'),
                    section: i18n._('Results')
                },
                results: {
                    labellabel: i18n._('Results'),
                    section: i18n._('Results')
                },
                start: {
                    labellabel: i18n._('Start'),
                    section: i18n._('Timing')
                },
                end: {
                    labellabel: i18n._('End'),
                    section: i18n._('Timing')
                },
                delta: {
                    labellabel: i18n._('Elapsed'),
                    section: i18n._('Timing')
                }
            }
        };}]);
