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
        searchWidgetLabel: 'Object',
        searchWidgetLabel2: 'Modified by',
        
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
                dataPlacement: 'top',
                searchPlaceholder: 'Username',
                searchWidget: 2
                },
            objects: {
                label: 'Objects',
                ngBindHtml: 'activity.objects',
                nosort: true,
                searchable: false
                },
            description: {
                label: 'Description',
                ngBindHtml: 'activity.description',
                nosort: true, 
                searchable: false
                },
            system_event: {
                label: 'System',
                searchOnly: true, 
                searchType: 'isnull',
                sourceModel: 'user',
                sourceField: 'username',
                searchWidget: 2
                },
            // The following fields exist to forces loading each type of object into the search
            // dropdown
            all_objects: {
                label: 'All',
                searchOnly: true, 
                searchObject: 'all',
                searchPlaceholder: ' '
                },
            credential_search: {
                label: 'Credential',
                searchOnly: true,
                searchObject: 'credentials',
                searchPlaceholder: 'Credential name'
                },
            group_search: {
                label: 'Group',
                searchOnly: true,
                searchObject: 'groups',
                searchPlaceholder: 'Group name'
                },
            host_search: {
                label: 'Host',
                searchOnly: true,
                searchObject: 'hosts',
                searchPlaceholder: 'Host name'
                },
            inventory_search: {
                label: 'Inventory',
                searchOnly: true,
                searchObject: 'inventories',
                searchPlaceholder: 'Inventory name'
                },
            job_template_search: {
                label: 'Job Template',
                searchOnly: true,
                searchObject: 'job_templates',
                searchPlaceholder: 'Job template name'
                },
            organization_search: {
                label: 'Organization',
                searchOnly: true,
                searchObject: 'organizations',
                searchPlaceholder: 'Organization name'
                },
            project_search: {
                label: 'Project',
                searchOnly: true,
                searchObject: 'projects',
                searchPlaceholder: 'Project name'
                },
            user_search: {
                label: 'User',
                searchOnly: true,
                searchObject: 'users',
                searchPlaceholder: 'Username'
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