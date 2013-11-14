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
            user: {
                label: 'User',
                linkTo: "\{\{ activity.userLink \}\}",
                sourceModel: 'user',
                sourceField: 'username',
                awToolTip: "\{\{ userToolTip \}\}",
                dataPlacement: 'top'
                },
            timestamp: {
                label: 'Event Time',
                },
            objects: {
                label: 'Objects',
                ngBindHtml: 'activity.objects'
                },
            description: {
                label: 'Description'
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
            }
        });