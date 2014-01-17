/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Stream.js 
 *
 *  Activity stream widget that can be called from anywhere
 *
 */

angular.module('StreamWidget', ['RestServices', 'Utilities', 'StreamListDefinition', 'SearchHelper', 'PaginateHelper',
        'RefreshHelper', 'ListGenerator', 'StreamWidget', 'AuthService'])
    
    .factory('setStreamHeight', [ function() {
    return function() {
        // Try not to overlap footer. Because stream is positioned absolute, the parent
        // doesn't resize correctly when stream is loaded.
        var stream = $('#stream-container');
        var height = stream.height() + 50;
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
        // There was some sort weirdness with the tab 'show' causing the stream to slide in when
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
        // Load the breadcrumbs array. We have to do things a bit different than our standing Utilities.LoadBreadcrumbs. 
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
               url += 'home/' + obj.base + 's/?name=' + obj.name;
               break;
           case 'inventory':
               url += 'inventories/' + obj.id;
               break;
           default:
               url += obj.base + 's/' + obj.id;
        }
        return url;
        }
        }])

    .factory('BuildDescription', ['FixUrl', 'BuildUrl', function(FixUrl, BuildUrl) {
    return function(activity) {
        var descr = '';
        var descr_nolink;
        descr += activity.operation;
        descr += (/e$/.test(activity.operation)) ? 'd ' : 'ed ';
        descr_nolink = descr;
        var obj1 = activity.object1;
        var obj2 = activity.object2;
        if (activity.summary_fields[obj2] && activity.summary_fields[obj2][0].name) {
            activity.summary_fields[obj2][0]['base'] = obj2;
            descr += obj2 + ' <a href=\"' + BuildUrl(activity.summary_fields[obj2][0]) + '\">'
                + activity.summary_fields[obj2][0].name + '</a>' + ( (activity.operation == 'disassociate') ? ' from ' : ' to ' ); 
            descr_nolink += obj2 + ' ' + activity.summary_fields[obj2][0].name + ( (activity.operation == 'disassociate') ? ' from ' : ' to ' );
        }
        else if (activity.object2) { 
            descr += activity.object2[0] + ( (activity.operation == 'disassociate') ? ' from ' : ' to ' );
            descr_nolink += activity.object2[0] + ( (activity.operation == 'disassociate') ? ' from ' : ' to ' );
        }
        if (activity.summary_fields[obj1] && activity.summary_fields[obj1][0].name) {
            activity.summary_fields[obj1][0]['base'] = obj1;
            descr += obj1 + ' <a href=\"' + BuildUrl(activity.summary_fields[obj1][0]) + '\">'
                + activity.summary_fields[obj1][0].name + '</a>';
            descr_nolink += obj1 + ' ' + activity.summary_fields[obj1][0].name; 
        }
        else if (activity.object1) { 
            descr += activity.object1;
            descr_nolink += activity.object1;
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
            activity['changes'] = JSON.stringify(activity['changes'], null, '\t'); 
            var n = activity['changes'].match(/\n/g);
            var rows = (n) ? n.length : 1;
            rows = (rows < 1) ? 3 : 10;
            form.fields['changes'].rows = 10;             
            
            // Load the form
            var scope = generator.inject(form, { mode: 'edit', modal: true, related: false });
            scope['changes'] = activity['changes'];
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
        'ShowDetail', 'StreamBreadCrumbs', 'setStreamHeight',
    function($rootScope, $location, Rest, GetBasePath, ProcessErrors, Wait, StreamList, SearchInit, PaginateInit, GenerateList,
        FormatDate, ShowStream, HideStream, BuildDescription, FixUrl, BuildUrl, ShowDetail, StreamBreadCrumbs, setStreamHeight) {
    return function(params) {
    
        var list = StreamList;
        var defaultUrl = GetBasePath('activity_stream');
        var view = GenerateList;
        var base = $location.path().replace(/^\//,'').split('/')[0];
        
        $rootScope.flashMessage = null;

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

        // Add a container for the stream widget
        $('#tab-content-container').append('<div id="stream-container"><div id=\"stream-content\"></div></div><!-- Stream widget -->');
        
        StreamBreadCrumbs();
        ShowStream();
        
        // Generate the list
        var scope = view.inject(list, { 
            mode: 'edit',
            id: 'stream-content', 
            breadCrumbs: true, 
            searchSize: 'col-lg-3',
            secondWidget: true,
            activityStream: true
            });

        scope.closeStream = function(inUrl) { 
            HideStream();
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
            for (var i=0; i < scope['activities'].length; i++) {
                // Convert event_time date to local time zone
                cDate = new Date(scope['activities'][i].timestamp);
                scope['activities'][i].timestamp = FormatDate(cDate);
                
                // Display username
                /*scope['activities'][i].user = (scope['activities'][i].summary_fields.user) ? scope['activities'][i].summary_fields.user.username :
                    'system';
                if (scope['activities'][i].user !== 'system') {
                    // turn user into a link when not 'system'
                    scope['activities'][i].user = "<a href=\"" + FixUrl(scope['activities'][i].related.user) + "\">" + 
                        scope['activities'][i].user + "</a>";
                }*/
                if (scope['activities'][i]['summary_fields']['actor']) {
                    scope['activities'][i]['user'] = "<a href=\"/#/users/" + scope['activities'][i]['summary_fields']['actor']['id'] + "\">" +
                        scope['activities'][i]['summary_fields']['actor']['username'] + "</a>";
                }
                else {
                    scope['activities'][i]['user'] = 'system';
                }
                
                // Objects
                var href;
                var deleted = /^\_delete/;
                var obj1 = scope['activities'][i].object1;
                var obj2 = scope['activities'][i].object2;
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
    