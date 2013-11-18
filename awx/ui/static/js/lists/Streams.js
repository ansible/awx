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
        searchWidgets: 3,
        
        fields: {
            timestamp: {
                label: 'Event Time',
                key: true,
                desc: true,
                noLink: true,
                searchable: false
                },
            user: {
                label: 'Initiated by',
                ngBindHtml: 'activity.user',
                sourceModel: 'user',
                sourceField: 'username',
                awToolTip: "\{\{ userToolTip \}\}",
                dataPlacement: 'top',
                searchPlaceholder: 'Initiated by username',
                searchWidget: 1
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
                label: 'System event',
                searchOnly: true, 
                searchType: 'isnull',
                sourceModel: 'user',
                sourceField: 'username',
                searchWidget: 1
                },

            // The following fields exist to force loading each type of object into the search
            // dropdown
            all_objects: {
                label: 'All',
                searchOnly: true, 
                searchObject: 'all',
                searchPlaceholder: 'All primary objects',
                searchWidget: 2,
                searchField: 'object1'
                },
            credential_search: {
                label: 'Credential',
                searchOnly: true,
                searchObject: 'credentials',
                searchPlaceholder: 'Primary credential name',
                searchWidget: 2,
                searchField: 'object1'
                },
            group_search: {
                label: 'Group',
                searchOnly: true,
                searchObject: 'groups',
                searchPlaceholder: 'Primary group name',
                searchWidget: 2,
                searchField: 'object1'
                },
            host_search: {
                label: 'Host',
                searchOnly: true,
                searchObject: 'hosts',
                searchPlaceholder: 'Primary host name',
                searchWidget: 2,
                searchField: 'object1'
                },
            inventory_search: {
                label: 'Inventory',
                searchOnly: true,
                searchObject: 'inventories',
                searchPlaceholder: 'Primary inventory name',
                searchWidget: 2,
                searchField: 'object1'
                },
            job_template_search: {
                label: 'Job Template',
                searchOnly: true,
                searchObject: 'job_templates',
                searchPlaceholder: 'Primary job template name',
                searchWidget: 2,
                searchField: 'object1'
                },
            organization_search: {
                label: 'Organization',
                searchOnly: true,
                searchObject: 'organizations',
                searchPlaceholder: 'Primary organization name',
                searchWidget: 2,
                searchField: 'object1'
                },
            project_search: {
                label: 'Project',
                searchOnly: true,
                searchObject: 'projects',
                searchPlaceholder: 'Primary project name',
                searchWidget: 2,
                searchField: 'object1'
                },
            user_search: {
                label: 'User',
                searchOnly: true,
                searchObject: 'users',
                searchPlaceholder: 'Primary username',
                searchWidget: 2,
                searchField: 'object1'
                },

            // The following fields exist to force loading each type of object into the search
            // dropdown
            all_objects3: {
                label: 'All',
                searchOnly: true, 
                searchObject: 'all',
                searchPlaceholder: 'All related objects',
                searchWidget: 3,
                searchField: 'object2'
                },
            credential_search3: {
                label: 'Credential',
                searchOnly: true,
                searchObject: 'credentials',
                searchPlaceholder: 'Related credential name',
                searchWidget: 3,
                searchField: 'object2'
                },
            group_search3: {
                label: 'Group',
                searchOnly: true,
                searchObject: 'groups',
                searchPlaceholder: 'Related group name',
                searchWidget: 3,
                searchField: 'object2'
                },
            host_search3: {
                label: 'Host',
                searchOnly: true,
                searchObject: 'hosts',
                searchPlaceholder: 'Related host name',
                searchWidget: 3,
                searchField: 'object2'
                },
            inventory_search3: {
                label: 'Inventory',
                searchOnly: true,
                searchObject: 'inventories',
                searchPlaceholder: 'Related inventory name',
                searchWidget: 3,
                searchField: 'object2'
                },
            job_template_search3: {
                label: 'Job Template',
                searchOnly: true,
                searchObject: 'job_templates',
                searchPlaceholder: 'Related job template name',
                searchWidget: 3,
                searchField: 'object2'
                },
            organization_search3: {
                label: 'Organization',
                searchOnly: true,
                searchObject: 'organizations',
                searchPlaceholder: 'Related organization name',
                searchWidget: 3,
                searchField: 'object2'
                },
            project_search3: {
                label: 'Project',
                searchOnly: true,
                searchObject: 'projects',
                searchPlaceholder: 'Related project name',
                searchWidget: 3,
                searchField: 'object2'
                },
            user_search3: {
                label: 'User',
                searchOnly: true,
                searchObject: 'users',
                searchPlaceholder: 'Related username',
                searchWidget: 3,
                searchField: 'object2'
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