/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Streams.js 
 *  List view object for activity stream data model.
 *
 * 
 */
angular.module('StreamListDefinition', [])
    .value(
    'StreamList', {
        
        name: 'activities',
        iterator: 'activity',
        editTitle: 'Activity Stream',
        selectInstructions: '', 
        index: false,
        hover: true,
        "class": "table-condensed",
        
        fields: {
            timestamp: {
                label: 'Event Time',
                key: true,
                desc: true,
                noLink: true,
                searchable: false
                },
            user: {
                label: 'User',
                ngBindHtml: 'activity.user',
                sourceModel: 'user',
                sourceField: 'username',
                awToolTip: "\{\{ userToolTip \}\}",
                dataPlacement: 'top'
                },
            objects: {
                label: 'Objects',
                ngBindHtml: 'activity.objects',
                sortField: "object1__name,object2__name",
                searchable: false
                },
            object_name: {
                label: 'Object name',
                searchOnly: true,
                searchType: 'or', 
                searchFields: ['object1__name', 'object2__name']
                },
            description: {
                label: 'Description',
                ngBindHtml: 'activity.description',
                nosort: true, 
                searchable: false
                },
            system_event: {
                label: 'System event?',
                searchOnly: true, 
                searchType: 'isnull',
                sourceModel: 'user',
                sourceField: 'username'
                }
            },
        
        actions: {
            refresh: {
                dataPlacement: 'top',
                icon: "icon-refresh",
                mode: 'all',
                'class': 'btn-xs btn-primary',
                awToolTip: "Refresh the page",
                ngClick: "refreshStream()",
                iconSize: 'large'
                },
            close: {
                dataPlacement: 'top',
                icon: "icon-arrow-left",
                mode: 'all',
                'class': 'btn-xs btn-primary',
                awToolTip: "Close Activity Stream view",
                ngClick: "closeStream()",
                iconSize: 'large'
                }
            },

        fieldActions: {
            edit: {
                label: 'View',
                ngClick: "showDetail(\{\{ activity.id \}\})",
                icon: 'icon-zoom-in',
                "class": 'btn-default btn-xs',
                awToolTip: 'View event details',
                dataPlacement: 'top'
                }
            }

        });