/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Streams.js
 *  List view object for activity stream data model.
 *
 *
 */



export default
    angular.module('StreamListDefinition', [])
    .value('StreamList', {

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
                searchable: false,
                filter: "date:'MM/dd/yy HH:mm:ss'"
            },
            user: {
                label: 'Initiated by',
                ngBindHtml: 'activity.user',
                sourceModel: 'actor',
                sourceField: 'username',
                //awToolTip: "\{\{ userToolTip \}\}",
                //dataPlacement: 'top',
                searchPlaceholder: 'Username',
                searchWidget: 1
            },
            description: {
                label: 'Action',
                ngBindHtml: 'activity.description',
                nosort: true,
                searchable: false,
                columnClass: 'col-lg-7'
            },
            actor: {
                label: 'System event',
                searchOnly: true,
                searchType: 'isnull',
                searchWidget: 1
            },

            // The following fields exist to force loading each type of object into the search
            // dropdown
            all_objects: {
                label: 'All',
                searchOnly: true,
                searchObject: 'all',
                searchPlaceholder: 'All resources',
                searchWidget: 2
            },
            credential_search: {
                label: 'Credential',
                searchOnly: true,
                searchObject: 'credential',
                searchPlaceholder: 'Credential name',
                searchWidget: 2,
                searchField: 'object1'
            },
            custom_inventory_search: {
                label: 'Custom Inventory Script',
                searchOnly: true,
                searchObject: 'custom_inventory_script',
                searchPlaceholder: 'Custom inventory script name',
                searchWidget: 2,
                searchField: 'object1'
            },
            group_search: {
                label: 'Group',
                searchOnly: true,
                searchObject: 'group',
                searchPlaceholder: 'Group name',
                searchWidget: 2,
                searchField: 'object1'
            },
            host_search: {
                label: 'Host',
                searchOnly: true,
                searchObject: 'host',
                searchPlaceholder: 'Host name',
                searchWidget: 2,
                searchField: 'object1'
            },
            inventory_search: {
                label: 'Inventory',
                searchOnly: true,
                searchObject: 'inventory',
                searchPlaceholder: 'Inventory name',
                searchWidget: 2,
                searchField: 'object1'
            },
            job_template_search: {
                label: 'Job Template',
                searchOnly: true,
                searchObject: 'job_template',
                searchPlaceholder: 'Job template name',
                searchWidget: 2,
                searchField: 'object1'
            },
            job_search: {
                label: 'Job',
                searchOnly: true,
                searchObject: 'job',
                searchPlaceholder: 'Job name',
                //searchOnID: true,
                searchWidget: 2,
                searchField: 'object1'
            },
            organization_search: {
                label: 'Organization',
                searchOnly: true,
                searchObject: 'organization',
                searchPlaceholder: 'Organization name',
                searchWidget: 2,
                searchField: 'object1'
            },
            project_search: {
                label: 'Project',
                searchOnly: true,
                searchObject: 'project',
                searchPlaceholder: 'Project name',
                searchWidget: 2,
                searchField: 'object1'
            },
            schedule_search: {
                label: 'Schedule',
                searchOnly: true,
                searchObject: 'schedule',
                searchPlaceholder: 'Schedule name',
                searchWidget: 2,
                searchField: 'object1'
            },
            user_search: {
                label: 'User',
                searchOnly: true,
                searchObject: 'user',
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
                searchPlaceholder: 'All related resources',
                searchWidget: 3,
                searchField: 'object2'
            },
            credential_search3: {
                label: 'Credential',
                searchOnly: true,
                searchObject: 'credential',
                searchPlaceholder: 'Related credential name',
                searchWidget: 3,
                searchField: 'object2'
            },
            custom_inventory_script_search3: {
                label: 'Custom Inventory Script',
                searchOnly: true,
                searchObject: 'custom_inventory_script',
                searchPlaceholder: 'Related custom inventory script name',
                searchWidget: 3,
                searchField: 'object2'
            },
            group_search3: {
                label: 'Group',
                searchOnly: true,
                searchObject: 'group',
                searchPlaceholder: 'Related group name',
                searchWidget: 3,
                searchField: 'object2'
            },
            host_search3: {
                label: 'Host',
                searchOnly: true,
                searchObject: 'host',
                searchPlaceholder: 'Related host name',
                searchWidget: 3,
                searchField: 'object2'
            },
            inventory_search3: {
                label: 'Inventory',
                searchOnly: true,
                searchObject: 'inventory',
                searchPlaceholder: 'Related inventory name',
                searchWidget: 3,
                searchField: 'object2'
            },
            job_search3: {
                label: 'Job',
                searchOnly: true,
                searchObject: 'job',
                searchPlaceholder: 'Related job name',
                //searchOnID: true,
                searchWidget: 3,
                searchField: 'object2'
            },
            job_template_search3: {
                label: 'Job Template',
                searchOnly: true,
                searchObject: 'job_template',
                searchPlaceholder: 'Related job template name',
                searchWidget: 3,
                searchField: 'object2'
            },
            organization_search3: {
                label: 'Organization',
                searchOnly: true,
                searchObject: 'organization',
                searchPlaceholder: 'Related organization name',
                searchWidget: 3,
                searchField: 'object2'
            },
            project_search3: {
                label: 'Project',
                searchOnly: true,
                searchObject: 'project',
                searchPlaceholder: 'Related project name',
                searchWidget: 3,
                searchField: 'object2'
            },
            schedule_search3: {
                label: 'Schedule',
                searchOnly: true,
                searchObject: 'schedule',
                searchPlaceholder: 'Schedule name',
                searchWidget: 3,
                searchField: 'object1'
            },
            user_search3: {
                label: 'User',
                searchOnly: true,
                searchObject: 'user',
                searchPlaceholder: 'Related username',
                searchWidget: 3,
                searchField: 'object2'
            }
        },

        actions: {
            refresh: {
                mode: 'all',
                id: 'activity-stream-refresh-btn',
                'class': 'btn-xs',
                awToolTip: "Refresh the page",
                ngClick: "refreshStream()"
            },
            close: {
                mode: 'all',
                awToolTip: "Close Activity Stream view",
                ngClick: "closeStream()"
            }
        },

        fieldActions: {
            view: {
                label: 'View',
                ngClick: "showDetail(activity.id)",
                icon: 'fa-zoom-in',
                "class": 'btn-default btn-xs',
                awToolTip: 'View event details',
                dataPlacement: 'top'
            }
        }

    });