/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


export default
    angular.module('StreamListDefinition', [])
    .value('StreamList', {

        name: 'activities',
        iterator: 'activity',
        basePath: 'activity_stream',
        editTitle: 'Activity Stream',
        listTitle: 'Activity Stream<span ng-show="streamSubTitle"><div class="List-titleLockup"></div>{{streamSubTitle}}<span>',
        listTitleBadge: false,
        emptyListText: 'There are no events to display at this time',
        selectInstructions: '',
        index: false,
        hover: true,
        "class": "table-condensed",
        toolbarAuxAction: "<stream-dropdown-nav></stream-dropdown-nav>",

        fields: {
            timestamp: {
                label: 'Time',
                key: true,
                desc: true,
                noLink: true,
                filter: "longDate",
                columnClass: 'col-lg-3 col-md-2 col-sm-3 col-xs-3'
            },
            user: {
                label: 'Initiated by',
                ngBindHtml: 'activity.user', // @todo punch monkey
                sourceModel: 'actor',
                sourceField: 'username',
                columnClass: 'col-lg-3 col-md-3 col-sm-3 col-xs-3'
            },
            description: {
                label: 'Event',
                ngBindHtml: 'activity.description', // @todo punch monkey
                nosort: true,
                columnClass: 'ActivityStream-eventColumnHeader col-lg-5 col-md-6 col-sm-4 col-xs-4'
            }
        },

        actions: {
            refresh: {
                mode: 'all',
                id: 'activity-stream-refresh-btn',
                awToolTip: "Refresh the page",
                ngClick: "refreshStream()",
                actionClass: 'btn List-buttonDefault ActivityStream-refreshButton',
                buttonContent: 'REFRESH'
            }
        },

        fieldActions: {

            columnClass: 'col-lg-1 col-md-1 col-sm-2 col-xs-2',

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
