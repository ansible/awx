/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  JobEvents.js
 *  Form definition for Job Events model
 *
 *
 */
angular.module('JobEventFormDefinition', [])
    .value(
    'JobEventForm', {
        
        editTitle: '{{ name }} Events',                         //Legend in edit mode
        name: 'job_events',
        well: true,
        fieldsAsHeader: true,
        
        fields: {
            job: {
                label: 'Job',
                type: 'text',
                class: 'span1',
                readonly: true
                },
            job_name: {
                type: 'text',
                sourceModel: 'job',
                sourceField: 'name',
                class: 'span5',
                readonly: true
                },
            job_description: { 
                type: 'text',
                sourceModel: 'job',
                sourceField: 'description',
                class: 'span5',
                readonly: true
                }
            },

        buttons: { 

            },

        items: {
            event: {
                set: 'job_events',
                iterator: 'job_event',
                label: 'Event',
                fields: {
                    id: {
                        label: 'Event ID',
                        type: 'text',
                        readonly: true,
                        class: 'span2',
                        key: true,
                        searchType: 'int'
                        },
                    created: {
                        label: 'Event Timestamp',
                        type: 'text',
                        readonly: true,
                        class: 'span4'
                        },
                    event: {
                        label: 'Event',
                        type: 'text',
                        readonly: true
                        },
                    host: {
                        label: 'Host',
                        type: 'text',
                        readonly: true
                        },
                    event_status: {
                        label: 'Event Status',
                        type: 'text',
                        class: 'job-\{\{ event_status \}\}',
                        readonly: true,
                        searchField: 'failed',
                        searchType: 'boolean',
                        searchOptions: [{ name: "success", value: 0 }, { name: "failed", value: 1 }],
                        },
                    event_data: {
                        label: 'Event Data',
                        type: 'textarea',
                        class: 'span12',
                        rows: 10,
                        readonly: true
                        } 
                    }
                }
            },
         
        related: { //related colletions (and maybe items?)
           
            }
            
    }); //Form

