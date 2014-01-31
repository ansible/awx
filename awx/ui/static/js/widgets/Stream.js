/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Stream.js 
 *
 *  Activity stream widget that can be called from anywhere
 *
 */

'use strict';

angular.module('StreamWidget', ['RestServices', 'Utilities', 'StreamListDefinition', 'SearchHelper', 'PaginationHelpers',
        'RefreshHelper', 'ListGenerator', 'StreamWidget', 'AuthService'])
    
    .factory('setStreamHeight', [ function() {
    return function() {
        // Try not to overlap footer. Because stream is positioned absolute, the parent
        // doesn't resize correctly when stream is loaded.
        var sheight = $('#stream-content').height();
        var theight = parseInt($('#tab-content-container').css('min-height').replace(/px/,''));
        var height = (theight < sheight) ? sheight : theight;
        $('#tab-content-container').css({ "min-height": height });
        }
        }])

    .factory('ShowStream', [ 'setStreamHeight', 'Authorization', function(setStreamHeight, Authorization) {
    return function() {
        // Slide in the Stream widget
        
        // Make some style/position adjustments adjustments
        var stream = $('#stream-container');
        stream.css({ 
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            'min-height': '100%',
            'background-color': '#FFF'
            });

        setStreamHeight();

        // Slide in stream
        stream.show('slide', {'direction': 'left'}, {'duration': 500, 'queue': false });
        
        }
        }])

    .factory('HideStream', [ 'LoadBreadCrumbs', function(LoadBreadCrumbs) {
    return function() {
        // Remove the stream widget
        
        var stream = $('#stream-container');
        stream.hide('slide', {'direction': 'left'}, {'duration': 500, 'queue': false }); 
        
        // Completely destroy the container so we don't experience random flashes of it later.
        // There was some sort of weirdness with the tab 'show' causing the stream to slide in when
        // a tab was clicked, after the stream had been hidden. Seemed like timing- wait long enough
        // before clicking a tab, and it would not happen.
        setTimeout( function() {
           stream.detach();
           stream.empty();
           stream.unbind();
           $('#tab-content-container').css({ 'min-height': 0 }); //let the parent height go back to normal
           }, 500);
        
        LoadBreadCrumbs();
        }
        }])

    .factory('StreamBreadCrumbs', ['$rootScope', '$location', function($rootScope, $location) { 
    return function() {
        // Load the breadcrumbs array. We have to do things a bit different than Utilities.LoadBreadcrumbs. 
        // Rather than botch that all up, we'll do our own thing here.
        $rootScope.breadcrumbs = [];
        var paths = $location.path().split('/');
        paths.splice(0,1);
        var path, title;
        for (var i=0; i < paths.length; i++) {
            if (/^\d+/.test(paths[i])) {
                path='';
                title='';
                for (j=0; j <= i; j++) {
                    path += '/' + paths[j];
                }
                for (j=0; j < $rootScope.crumbCache.length; j++) {
                    if ($rootScope.crumbCache[j].path == path) {
                        title = $rootScope.crumbCache[j].title;
                        break;
                    }
                }
                if (!title) {
                    title = paths[i - 1].substr(0,paths[i - 1].length - 1);
                    title = (title == 'inventorie') ? 'inventory' : title;
                }
            }
            else {
                path='';
                title='';
                if (i > 0) {
                    for (j=0; j <= i; j++) {
                        path += '/' + paths[j];
                    }
                }
                else {
                   path = '/' + paths[i];
                }
                title = paths[i];
            }
            $rootScope.breadcrumbs.push({ path: path, title: title, ngClick: "closeStream('" + path + "')" });    
        }
        }
        }])

    .factory('FixUrl', [ function() {
    return function(u) {
        return u.replace(/\/api\/v1\//,'/#/');
        }
        }])

    .factory('BuildUrl', [ function() {
    return function(obj) {
        var url = '/#/';
        switch(obj.base) {
           case 'group':
           case 'host': 
               url += 'home/' + obj.base + 's/?id=' + obj.id;
               break;
           case 'inventory':
               url += 'inventories/' + obj.id + '/';
               break;
           default:
               url += obj.base + 's/' + obj.id + '/';
        }
        return url;
        }
        }])

    .factory('BuildDescription', ['FixUrl', 'BuildUrl', function(FixUrl, BuildUrl) {
    return function(activity) {
        
        function stripDeleted(s) {
            return s.replace(/^_deleted_\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d+\+\d+:\d+_/,'');
            }
        
        var descr = '';
        var descr_nolink;
        descr += activity.operation;
        descr += (/e$/.test(activity.operation)) ? 'd ' : 'ed ';
        descr_nolink = descr;

        // labels
        var obj1 = activity.object1;
        var obj2 = activity.object2;
        
        // objects
        var obj1_obj = (activity.summary_fields[obj1]) ? activity.summary_fields[obj1][0] : null;
        if (obj1 == obj2) {
            var obj2_obj = activity.summary_fields[obj1][1];
        }
        else if (activity.summary_fields[obj2]) {
            var obj2_obj = activity.summary_fields[obj2][0];
        }
        else { 
            var obj2_obj = null;
        }
        
        if (obj1 == 'user' || obj2 == 'user') {
            activity.summary_fields['user'][0].name = activity.summary_fields['user'][0].username;
        }
        
        var name;
        if (obj2_obj && obj2_obj.name && !/^_delete/.test(obj2_obj.name)) {
            obj2_obj['base'] = obj2;
            descr += obj2 + ' <a href=\"' + BuildUrl(obj2_obj) + '\">'
                + obj2_obj.name  + '</a>' + ( (activity.operation == 'disassociate') ? ' from ' : ' to ' ); 
            descr_nolink += obj2 + ' ' + obj2_obj.name + ( (activity.operation == 'disassociate') ? ' from ' : ' to ' );
        }
        else if (obj2) {
            name = '';
            if (obj2_obj && obj2_obj.name) {
                name = ' ' + stripDeleted(obj2_obj.name);
            }
            descr += obj2 + name + ( (activity.operation == 'disassociate') ? ' from ' : ' to ' );
            descr_nolink += obj2 + name + ( (activity.operation == 'disassociate') ? ' from ' : ' to ' );
        }
        if (obj1_obj && obj1_obj.name && !/^\_delete/.test(obj1_obj.name)) {     
            obj1_obj['base'] = obj1;
            descr += obj1 + ' <a href=\"' + BuildUrl(obj1_obj) + '\">' + obj1_obj.name + '</a>';
            descr_nolink += obj1 + ' ' + obj1_obj.name; 
        }
        else if (obj1) {
            name = '';
            var name_nolink = '';
            // find the name in changes, if needed
            if ( !(obj1_obj && obj1_obj.name) || obj1_obj && obj1_obj.name && /^_delete/.test(obj1_obj.name) ) {
                if (activity.changes && activity.changes.name) {
                    if (typeof activity.changes.name == 'string') {
                        name = ' ' + activity.changes.name;
                        name_nolink = name;
                    }
                    else if (typeof activity.changes.name == 'object' && Array.isArray(activity.changes.name)) {
                        name = ' ' + activity.changes.name[0];
                        name_nolink = name;
                    }
                }
                else if (obj1 == 'job' && obj1_obj && activity.changes && activity.changes.job_template) {
                    // Hack for job activity where the template name is known
                    if (activity.operation != 'delete') {
                        obj1_obj['base'] = obj1;
                        name = ' ' + '<a href=\"' + BuildUrl(obj1_obj) + '\">'+ obj1_obj.id + ' ' + activity.changes.job_template + '</a>';
                        name_nolink = ' ' + obj1_obj.id + ' ' + activity.changes.job_template;
                    }
                    else {
                        name = ' ' + obj1_obj.id + ' ' + activity.changes.job_template;
                        name_nolink = name;
                    }
                }
                else if (obj1 == 'job' && obj1_obj) {
                    // Hack for job activity where template name not known
                    if (activity.operation != 'delete') {
                        obj1_obj['base'] = obj1;
                        name = ' ' + '<a href=\"' + BuildUrl(obj1_obj) + '\">' + obj1_obj.id + '</a>';
                        name_nolink = ' ' + obj1_obj.id;
                    }
                    else {
                        name = ' ' + obj1_obj.id;
                        name_nolink = name;
                    }
                }
            }
            else if (obj1_obj && obj1_obj.name) {
                name = ' ' + stripDeleted(obj1_obj.name);
                name_nolink = name;
            }
            descr += obj1 + name;
            descr_nolink += obj1 + name_nolink;
        }
        activity['description'] = descr;
        activity['description_nolink'] = descr_nolink;
        }
        }])

    .factory('ShowDetail', ['$rootScope', 'Rest', 'Alert', 'GenerateForm', 'ProcessErrors', 'GetBasePath', 'FormatDate', 
        'ActivityDetailForm', 'Empty', 'Find',
    function($rootScope, Rest, Alert, GenerateForm, ProcessErrors, GetBasePath, FormatDate, ActivityDetailForm, Empty, Find) {
    return function(params) {

        var activity_id = params.activity_id;
        var parent_scope = params.scope;
        
        var generator = GenerateForm;
        var form = ActivityDetailForm;
        var activity = Find({list: parent_scope.activities, key: 'id', val: activity_id });

        if (activity) {
            // Setup changes field 
            activity['changes_stringified'] = JSON.stringify(activity['changes'], null, '\t'); 
            var n = activity['changes_stringified'].match(/\n/g);
            var rows = (n) ? n.length : 1;
            rows = (rows < 1) ? 3 : 10;
            form.fields['changes'].rows = 10;             
            
            // Load the form
            var scope = generator.inject(form, { mode: 'edit', modal: true, related: false });
            scope['changes'] = activity['changes_stringified'];
            scope['user'] = ( (activity.summary_fields.actor) ? activity.summary_fields.actor.username : 'system' ) +
                ' on ' + FormatDate(new Date(activity['timestamp']));
            scope['operation'] = activity['description_nolink'];
            
            scope.formModalAction = function() {
                $('#form-modal').modal("hide");
                }
            
            $('#form-modal').on('show.bs.modal', function (e) {
                $('#form-modal-body').css({
                    width:'auto',  //probably not needed
                    height:'auto', //probably not needed 
                    'max-height':'100%'
                    });
                });

            scope.formModalActionLabel = 'OK';
            scope.formModalCancelShow = false;
            scope.formModalInfo = false;
            scope.formModalHeader = "Event " + activity.id;
            
            if (!scope.$$phase) {
               scope.$digest();
            }
        }

        }
        }])

    .factory('Stream', ['$rootScope', '$location', 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait', 'StreamList', 'SearchInit', 
        'PaginateInit', 'GenerateList', 'FormatDate', 'ShowStream', 'HideStream', 'BuildDescription', 'FixUrl', 'BuildUrl', 
        'ShowDetail', 'StreamBreadCrumbs', 'setStreamHeight', 'Find', 'Store',
    function($rootScope, $location, Rest, GetBasePath, ProcessErrors, Wait, StreamList, SearchInit, PaginateInit, GenerateList,
        FormatDate, ShowStream, HideStream, BuildDescription, FixUrl, BuildUrl, ShowDetail, StreamBreadCrumbs, setStreamHeight,
        Find, Store) {
    return function(params) {
    
        var list = StreamList;
        var defaultUrl = GetBasePath('activity_stream');
        var view = GenerateList;
        var base = $location.path().replace(/^\//,'').split('/')[0];
        var parent_scope = params.scope;

        // Hang onto current search params
        var PreviousSearchParams = Store('CurrentSearchParams');

        // pass in an inventory name to fix breadcrumb display
        var inventory_name = (params && params.inventory_name) ? params.inventory_name : null;

        // url will override the attempt to compute an activity_stream query
        var url = (params && params.url) ? params.url : null;
        
        $rootScope.flashMessage = null;
        
        if (url) {
            defaultUrl = url;
        }
        else {
            if ($location.path() !== '/home') {
                // Restrict what we're looking at based on the path
                var type = (base == 'inventories') ? 'inventory' : base.replace(/s$/,'');
                var paths = $location.path().split('/');
                paths.splice(0,1);
                if (paths.length > 1 && /^\d+/.test(paths[paths.length - 1])) {
                    type = paths[paths.length - 2];
                    type = (type == 'inventories') ? 'inventory' : type.replace(/s$/,'');
                    //defaultUrl += '?object1=' + type + '&object1__id=' + 
                    defaultUrl += '?' + type + '__id=' + paths[paths.length - 1];
                }
                else if (paths.length > 1) {
                    type = paths[paths.length - 1];
                    type = (type == 'inventories') ? 'inventory' : type.replace(/s$/,'');
                    defaultUrl += '?or__object1=' + type + '&or__object2=' + type;
                }
                else {
                    defaultUrl += '?or__object1=' + type + '&or__object2=' + type;
                }
            }
        }

        // Add a container for the stream widget
        $('#tab-content-container').append('<div id="stream-container"><div id=\"stream-content\"></div></div><!-- Stream widget -->');
        
        StreamBreadCrumbs();

        // Fix inventory name. The way we're doing breadcrumbs doesn't support bind variables.
        if (inventory_name) {
            var itm = Find({ list: $rootScope.breadcrumbs, key: 'title', val: '{{ inventory_name }}' });
            if (itm) {
                itm.title = inventory_name;
            }
        }

        ShowStream();
        
        // Generate the list
        var scope = view.inject(list, { 
            mode: 'edit',
            id: 'stream-content', 
            searchSize: 'col-lg-3',
            secondWidget: true,
            activityStream: true
            });

        // descriptive title describing what AS is showing
        scope.streamTitle = (params && params.title) ? params.title : null;
        
        scope.closeStream = function(inUrl) { 
            HideStream();
            if (scope.searchCleanup) {
                scope.searchCleanup();
            }
            // Restore prior search state
            if (PreviousSearchParams) {
                SearchInit({
                    scope: parent_scope,
                    set: PreviousSearchParams.set,
                    list: PreviousSearchParams.list,
                    url: PreviousSearchParams.defaultUrl, 
                    iterator: PreviousSearchParams.iterator,
                    sort_order: PreviousSearchParams.sort_order,
                    setWidgets: false });
            }
            if (inUrl) {
               $location.path(inUrl);
            }
            }

        scope.refreshStream = function() {
            scope.search(list.iterator);
            }

        scope.showDetail = function(id) {
            ShowDetail({ scope: scope, activity_id: id });
            }

        if (scope.removeStreamPostRefresh) {
            scope.removeStreamPostRefresh();    
        }
        scope.removeStreamPostRefresh = scope.$on('PostRefresh', function() {
            var cDate, href, deleted, obj1, obj2;
            for (var i=0; i < scope['activities'].length; i++) {
                // Convert event_time date to local time zone
                cDate = new Date(scope['activities'][i].timestamp);
                scope['activities'][i].timestamp = FormatDate(cDate);
                
                if (scope['activities'][i]['summary_fields']['actor']) {
                    scope['activities'][i]['user'] = "<a href=\"/#/users/" + scope['activities'][i]['summary_fields']['actor']['id'] + "\">" +
                        scope['activities'][i]['summary_fields']['actor']['username'] + "</a>";
                }
                else {
                    scope['activities'][i]['user'] = 'system';
                }
                
                // Objects
                deleted = /^\_delete/;
                obj1 = scope['activities'][i].object1;
                obj2 = scope['activities'][i].object2;
                if ( obj1 && scope['activities'][i].summary_fields[obj1] && scope['activities'][i].summary_fields[obj1].name) {
                    if ( !deleted.test(scope['activities'][i].summary_fields[obj1].name) ) {
                        href = BuildUrl(scope['activities'][i].summary_fields.object1);
                        scope['activities'][i].objects = "<a href=\"" + href + "\">" + scope['activities'][i].summary_fields[obj1].name + "</a>";
                    }
                    else {
                        scope['activities'][i].objects = scope['activities'][i].summary_fields[obj1].name;
                    }
                }
                else if (scope['activities'][i].object1) {
                    scope['activities'][i].objects = scope['activities'][i].object1;
                }
                if (obj2 && scope['activities'][i].summary_fields[obj2] && scope['activities'][i].summary_fields[obj2].name) {
                    if ( !deleted.test(scope['activities'][i].summary_fields.object2.name) ) {
                        href = BuildUrl(scope['activities'][i].summary_fields.object2);
                        scope['activities'][i].objects += ", <a href=\"" + href + "\">" + scope['activities'][i].summary_fields[obj2].name + "</a>";
                    }
                    else {
                        scope['activities'][i].objects += "," + scope['activities'][i].summary_fields[obj2].name;
                    }
                }
                else if (scope['activities'][i].object2) {
                    scope['activities'][i].objects += ", " + scope['activities'][i].object2;
                }

                BuildDescription(scope['activities'][i]);

            }
            // Give ng-repeate a chance to show the data before adjusting the page size.
            setTimeout(function() { setStreamHeight(); }, 500);
            });
        
        // Initialize search and paginate pieces and load data
        SearchInit({ scope: scope, set: list.name, list: list, url: defaultUrl });
        PaginateInit({ scope: scope, list: list, url: defaultUrl });
        scope.search(list.iterator);

        }
        }]);
    
