/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


    /**
 * @ngdoc function
 * @name widgets.function:Stream
 * @description
 *  Stream.js
 *
 *  Activity stream widget that can be called from anywhere
 *
 */

import listGenerator from '../shared/list-generator/main';


angular.module('StreamWidget', ['RestServices', 'Utilities', 'StreamListDefinition', 'SearchHelper', 'PaginationHelpers',
    'RefreshHelper', listGenerator.name, 'StreamWidget',
])

.factory('setStreamHeight', [
    function () {
        return function () {
            // Try not to overlap footer. Because stream is positioned absolute, the parent
            // doesn't resize correctly when stream is loaded.
            var sheight = $('#stream-content').height(),
                theight = parseInt($('#main-view').css('min-height').replace(/px/, '')),
                height = (theight < sheight) ? sheight : theight;
            $('#main-view').css({
                "min-height": height
            });
        };
    }
])

.factory('FixUrl', [
    function () {
        return function (u) {
            return u.replace(/\/api\/v1\//, '/#/');
        };
    }
])

.factory('BuildUrl', [
    function () {
        return function (obj) {
            var url = '/#/';
            switch (obj.base) {
                case 'group':
                case 'host':
                    url += 'home/' + obj.base + 's/?id=' + obj.id;
                    break;
                case 'job':
                    url += 'jobs/?id__int=' + obj.id;
                    break;
                case 'inventory':
                    url += 'inventories/' + obj.id + '/';
                    break;
                case 'schedule':
                    url = (obj.url) ? '/#' + obj.url : '';
                    break;
                default:
                    url += obj.base + 's/' + obj.id + '/';
            }
            return url;
        };
    }
])

.factory('BuildDescription', ['$filter', 'FixUrl', 'BuildUrl','$sce',
    function ($filter, FixUrl, BuildUrl, $sce) {
        return function (activity) {

            function stripDeleted(s) {
                return s.replace(/^_deleted_\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d+\+\d+:\d+_/, '');
            }

            var descr, descr_nolink, obj1, obj2, obj1_obj, obj2_obj, name, name_nolink;

            descr = activity.operation;
            descr += (/e$/.test(activity.operation)) ? 'd ' : 'ed ';
            descr_nolink = descr;

            // labels
            obj1 = activity.object1;
            obj2 = activity.object2;

            // objects
            obj1_obj = (activity.summary_fields[obj1]) ? activity.summary_fields[obj1][0] : null;
            if (obj1 === obj2) {
                obj2_obj = activity.summary_fields[obj1][1];
            } else if (activity.summary_fields[obj2]) {
                obj2_obj = activity.summary_fields[obj2][0];
            } else {
                obj2_obj = null;
            }

            if (obj1 === 'user' || obj2 === 'user') {
                activity.summary_fields.user[0].name = activity.summary_fields.user[0].username;
            }
            // The block until line 221 is for associative/disassociative operations, such as adding/removing a user to a team or vise versa
            if (obj2_obj && obj2_obj.name && !/^_delete/.test(obj2_obj.name)) {
                obj2_obj.base = obj2;
                obj2_obj.name = $filter('sanitize')(obj2_obj.name);
                descr += obj2 +
                    " <a href=\"" + BuildUrl(obj2_obj) + "\">" +
                    obj2_obj.name + '</a>';
                if (activity.object_association === 'admins') {
                    if (activity.operation === 'disassociate') {
                        descr += ' from being an admin of ';
                    } else {
                        descr += ' as an admin of ';
                    }
                } else {
                    if (activity.operation === 'disassociate') {
                        descr += ' from ';
                    } else {
                        descr += ' to ';
                    }
                }
                descr_nolink += obj2 + ' ' + obj2_obj.name;
                if (activity.object_association === 'admins') {
                    if (activity.operation === 'disassociate') {
                        descr_nolink += ' from being an admin of ';
                    } else {
                        descr_nolink += ' as an admin of ';
                    }
                } else {
                    if (activity.operation === 'disassociate') {
                        descr_nolink += ' from ';
                    } else {
                        descr_nolink += ' to ';
                    }
                }
            } else if (obj2) {
                name = '';
                if (obj2_obj && obj2_obj.name) {
                    name = ' ' + stripDeleted(obj2_obj.name);
                }
                if (activity.object_association === 'admins') {
                    if (activity.operation === 'disassociate') {
                        descr += ' from being an admin of ';
                    } else {
                        descr += ' as an admin of ';
                    }
                } else {
                    if (activity.operation === 'disassociate') {
                        descr += ' from ';
                    } else {
                        descr += ' to ';
                    }
                }
                descr_nolink += (obj2_obj && obj2_obj.name) ? obj2 + ' ' + obj2_obj.name : obj2 + ' ';
                if (activity.object_association === 'admins') {
                    if (activity.operation === 'disassociate') {
                        descr_nolink += ' from being an admin of ';
                    } else {
                        descr_nolink += ' as an admin of ';
                    }
                } else {
                    if (activity.operation === 'disassociate') {
                        descr_nolink += ' from ';
                    } else {
                        descr_nolink += ' to ';
                    }
                }
            }
            if (obj1_obj && obj1_obj.name && !/^\_delete/.test(obj1_obj.name)) {
                obj1_obj.base = obj1;
                // Need to character escape the link names, as a malicious url or piece of html could be inserted here that could take the
                // user to a unknown location.
                obj1_obj.name = $filter('sanitize')(obj1_obj.name);
                obj1_obj.name = $sce.getTrustedHtml(obj1_obj.name);
                descr += obj1 + " <a href=\"" + BuildUrl(obj1_obj) + "\" >" + obj1_obj.name + '</a>';
                descr_nolink += obj1 + ' ' + obj1_obj.name;
            } else if (obj1) {
                name = '';
                name_nolink = '';
                // find the name in changes, if needed
                if (!(obj1_obj && obj1_obj.name) || obj1_obj && obj1_obj.name && /^_delete/.test(obj1_obj.name)) {
                    if (activity.changes && activity.changes.name) {
                        if (typeof activity.changes.name === 'string') {
                            name = ' ' + activity.changes.name;
                            name_nolink = name;
                        } else if (typeof activity.changes.name === 'object' && Array.isArray(activity.changes.name)) {
                            name = ' ' + activity.changes.name[0];
                            name_nolink = name;
                        }
                    /*} else if (obj1 === 'job' && obj1_obj && activity.changes && activity.changes.job_template) {
                        // Hack for job activity where the template name is known
                        if (activity.operation !== 'delete') {
                            obj1_obj.base = obj1;
                            name = ' ' + '<a href=\"' + BuildUrl(obj1_obj) + '\">' + obj1_obj.id + ' ' + activity.changes.job_template + '</a>';
                            name_nolink = ' ' + obj1_obj.id + ' ' + activity.changes.job_template;
                        } else {
                            name = ' ' + obj1_obj.id + ' ' + activity.changes.job_template;
                            name_nolink = name;
                        }
                    } else if (obj1 === 'job' && obj1_obj) {
                        // Hack for job activity where template name not known
                        if (activity.operation !== 'delete') {
                            obj1_obj.base = obj1;
                            name = ' ' + '<a href=\"' + BuildUrl(obj1_obj) + '\">' + obj1_obj.id + '</a>';
                            name_nolink = ' ' + obj1_obj.id;
                        } else {
                            name = ' ' + obj1_obj.id;
                            name_nolink = name;
                        }*/
                    }
                } else if (obj1_obj && obj1_obj.name) {
                    name = ' ' + stripDeleted(obj1_obj.name);
                    name_nolink = name;
                }
                descr += obj1 + name;
                descr_nolink += obj1 + name_nolink;
            }
            activity.description = descr;
            activity.description_nolink = descr_nolink;
        };
    }
])

.factory('ShowDetail', ['$filter', '$rootScope', 'Rest', 'Alert', 'GenerateForm', 'ProcessErrors', 'GetBasePath', 'FormatDate',
    'ActivityDetailForm', 'Empty', 'Find',
    function ($filter, $rootScope, Rest, Alert, GenerateForm, ProcessErrors, GetBasePath, FormatDate, ActivityDetailForm, Empty, Find) {
        return function (params) {

            var activity_id = params.activity_id,
                parent_scope = params.scope,
                activity = Find({ list: parent_scope.activities, key: 'id', val: activity_id }),
                scope, element;

            if (activity) {

                // Grab our element out of the dom
                element = angular.element(document.getElementById('stream-detail-modal'));

                // Grab the modal's scope so that we can set a few variables
                scope = element.scope();

                scope.changes = activity.changes;
                scope.user = ((activity.summary_fields.actor) ? activity.summary_fields.actor.username : 'system') +
                     ' on ' + $filter('longDate')(activity.timestamp);
                scope.operation = activity.description_nolink;
                scope.header = "Event " + activity.id;

                // Open the modal
                $('#stream-detail-modal').modal({
                    show: true,
                    backdrop: 'static',
                    keyboard: true
                });

                if (!scope.$$phase) {
                    scope.$digest();
                }
            }
        };
    }
])

.factory('Stream', ['$rootScope', '$location', '$state', 'Rest', 'GetBasePath',
    'ProcessErrors', 'Wait', 'StreamList', 'SearchInit', 'PaginateInit',
    'generateList', 'FormatDate', 'BuildDescription', 'FixUrl', 'BuildUrl',
    'ShowDetail', 'setStreamHeight',
    function ($rootScope, $location, $state, Rest, GetBasePath, ProcessErrors,
        Wait, StreamList, SearchInit, PaginateInit, GenerateList, FormatDate,
        BuildDescription, FixUrl, BuildUrl, ShowDetail, setStreamHeight) {
        return function (params) {

            var list = _.cloneDeep(StreamList),
                defaultUrl = GetBasePath('activity_stream'),
                view = GenerateList,
                parent_scope = params.scope,
                scope = parent_scope.$new(),
                url = (params && params.url) ? params.url : null;

            $rootScope.flashMessage = null;

            if (url) {
                defaultUrl = url;
            } else {

                if($state.params && $state.params.target) {
                    if($state.params.id) {
                        // We have a type and an ID
                        defaultUrl += '?' + $state.params.target + '__id=' + $state.params.id;
                    }
                    else {
                        // We just have a type
                        if ($state.params.target === 'inventory_script') {
                            defaultUrl += '?or__object1=custom_inventory_script&or__object2=custom_inventory_script';
                        } else if ($state.params.target === 'management_job') {
                            defaultUrl += '?or__object1=job&or__object2=job';
                        } else {
                            defaultUrl += '?or__object1=' + $state.params.target + '&or__object2=' + $state.params.target;
                        }
                    }
                }
            }

            if ($state.params.target === 'credential') {
                list.fields.customSearchField = {
                    label: 'Credential',
                    searchType: 'text',
                    searchOnly: 'true',
                    sourceModel: 'credential',
                    sourceField: 'name'
                };
            } else if ($state.params.target === 'host') {
                list.fields.customSearchField = {
                    label: 'Host',
                    searchType: 'text',
                    searchOnly: 'true',
                    sourceModel: 'host',
                    sourceField: 'name'
                };
            } else if ($state.params.target === 'inventory') {
                list.fields.customSearchField = {
                    label: 'Inventory',
                    searchType: 'text',
                    searchOnly: 'true',
                    sourceModel: 'inventory',
                    sourceField: 'name'
                };
            } else if ($state.params.target === 'inventory_script') {
                list.fields.customSearchField = {
                    label: 'Inventory Script',
                    searchType: 'text',
                    searchOnly: 'true',
                    sourceModel: 'custom_inventory_script',
                    sourceField: 'name'
                };
            } else if ($state.params.target === 'job_template') {
                list.fields.customSearchField = {
                    label: 'Job Template',
                    searchType: 'text',
                    searchOnly: 'true',
                    sourceModel: 'job_template',
                    sourceField: 'name'
                };
            } else if ($state.params.target === 'job') {
                list.fields.customSearchField = {
                    label: 'Job',
                    searchType: 'text',
                    searchOnly: 'true',
                    sourceModel: 'job',
                    sourceField: 'name'
                };
            } else if ($state.params.target === 'organization') {
                list.fields.customSearchField = {
                    label: 'Organization',
                    searchType: 'text',
                    searchOnly: 'true',
                    sourceModel: 'organization',
                    sourceField: 'name'
                };
            } else if ($state.params.target === 'project') {
                list.fields.customSearchField = {
                    label: 'Project',
                    searchType: 'text',
                    searchOnly: 'true',
                    sourceModel: 'project',
                    sourceField: 'name'
                };
            } else if ($state.params.target === 'schedule') {
                list.fields.customSearchField = {
                    label: 'Schedule',
                    searchType: 'text',
                    searchOnly: 'true',
                    sourceModel: 'schedule',
                    sourceField: 'name'
                };
            } else if ($state.params.target === 'team') {
                list.fields.customSearchField = {
                    label: 'Team',
                    searchType: 'text',
                    searchOnly: 'true',
                    sourceModel: 'team',
                    sourceField: 'name'
                };
            } else if ($state.params.target === 'user') {
                list.fields.customSearchField = {
                    label: 'User',
                    searchType: 'text',
                    searchOnly: 'true',
                    sourceModel: 'user',
                    sourceField: 'username'
                };
            }

            list.basePath = defaultUrl;

            // Generate the list
            view.inject(list, { mode: 'edit', id: 'stream-content', searchSize: 'col-lg-4 col-md-4 col-sm-12 col-xs-12', secondWidget: true, activityStream: true, scope: scope });

            // descriptive title describing what AS is showing
            scope.streamTitle = (params && params.title) ? params.title : null;

            scope.refreshStream = function () {
                scope.search(list.iterator);
            };

            scope.showDetail = function (id) {
                ShowDetail({
                    scope: scope,
                    activity_id: id
                });
            };

            if (scope.removeStreamPostRefresh) {
                scope.removeStreamPostRefresh();
            }
            scope.removeStreamPostRefresh = scope.$on('PostRefresh', function () {
                var href, deleted, obj1, obj2;
                scope.activities.forEach(function(activity, i) {
                    var row = scope.activities[i],
                        type, url;

                    if (scope.activities[i].summary_fields.actor) {
                        scope.activities[i].user = "<a href=\"/#/users/" + scope.activities[i].summary_fields.actor.id  + "\">" +
                            scope.activities[i].summary_fields.actor.username + "</a>";
                    } else {
                        scope.activities[i].user = 'system';
                    }

                    // Objects
                    deleted = /^\_delete/;
                    obj1 = scope.activities[i].object1;
                    obj2 = scope.activities[i].object2;

                    if ((obj1 === "schedule" || obj2 === "schedule") && activity.summary_fields.schedule) {
                        if (activity.summary_fields.inventory_source) {
                            type = 'inventory_source';
                            url = '/home/groups/?inventory_source__id=' + row.summary_fields.inventory_source.id;
                        }
                        else if (activity.summary_fields.project) {
                            type = 'project';
                            url = '/projects/' + activity.summary_fields[type].id + '/schedules/?id__int=';
                        }
                        else if (activity.summary_fields.system_job_template) {
                            type = 'system_job_template';
                            url = '/system_job_templates/' + activity.summary_fields[type].id + '/schedules/?id__int=';
                        }
                        else if (activity.summary_fields.job_template) {
                            type = 'job_template';
                            url = '/job_templates/' + activity.summary_fields[type].id + '/schedules/?id__int=';
                        }
                        if (obj1 === 'schedule') {
                            row.summary_fields.schedule[0].url = url + ((type === 'inventory_source') ? '' : row.summary_fields.schedule[0].id);
                            row.summary_fields.schedule[0].type = type;
                            row.summary_fields.schedule[0].type_id = activity.summary_fields[type].id;
                            row.summary_fields.schedule[0].base = 'schedule';
                        }
                        if (obj2 === 'schedule') {
                            row.summary_fields.schedule[1].url = url + ((type === 'inventory_source') ? '' : row.summary_fields.schedule[1].id);
                            row.summary_fields.schedule[1].type = type;
                            row.summary_fields.schedule[1].type_id = activity.summary_fields[type].id;
                            row.summary_fields.schedule[1].base = 'schedule';
                        }
                    }

                    if (obj1 && scope.activities[i].summary_fields[obj1] && scope.activities[i].summary_fields[obj1].name) {
                        if (!deleted.test(scope.activities[i].summary_fields[obj1].name)) {
                            href = BuildUrl(scope.activities[i].summary_fields[obj1]);
                            scope.activities[i].objects = "<a href=\"" + href + "\">" + scope.activities[i].summary_fields[obj1].name + "</a>";
                        } else {
                            scope.activities[i].objects = scope.activities[i].summary_fields[obj1].name;
                        }
                    } else if (scope.activities[i].object1) {
                        scope.activities[i].objects = scope.activities[i].object1;
                    }
                    if (obj2 && scope.activities[i].summary_fields[obj2] && scope.activities[i].summary_fields[obj2].name) {
                        if (!deleted.test(scope.activities[i].summary_fields[obj2].name)) {
                            href = BuildUrl(scope.activities[i].summary_fields[obj2]);
                            scope.activities[i].objects += ", <a href=\"" + href + "\">" + scope.activities[i].summary_fields[obj2].name + "</a>";
                        } else {
                            scope.activities[i].objects += "," + scope.activities[i].summary_fields[obj2].name;
                        }
                    } else if (scope.activities[i].object2) {
                        scope.activities[i].objects += ", " + scope.activities[i].object2;
                    }

                    BuildDescription(scope.activities[i]);

                });
                // Give ng-repeate a chance to show the data before adjusting the page size.
                setTimeout(function () {
                    setStreamHeight();
                }, 500);
            });

            // Initialize search and paginate pieces and load data
            SearchInit({
                scope: scope,
                set: list.name,
                list: list,
                url: defaultUrl
            });
            PaginateInit({
                scope: scope,
                list: list,
                url: defaultUrl
            });
            scope.search(list.iterator);
        };
    }
]);
