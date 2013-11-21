/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
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
        /*if (activity.summary_fields.user) {
            // this is a user transaction
            var usr = FixUrl(activity.related.user);
            descr += 'User <a href=\"' + usr + '\">' + activity.summary_fields.user.username + '</a> ';
        }
        else {
            descr += 'System '; 
        }*/
        descr += activity.operation;
        descr += (/e$/.test(activity.operation)) ? 'd ' : 'ed ';
        if (activity.summary_fields.object2 && activity.summary_fields.object2.name) {
            descr += activity.summary_fields.object2.base + ' <a href=\"' + BuildUrl(activity.summary_fields.object2) + '\">'
                + activity.summary_fields.object2.name + '</a>' + [ (activity.operation == 'disassociate') ? ' from ' : ' to ']; 
        }
        else if (activity.object2) { 
            descr += activity.object2 + [ (activity.operation == 'disassociate') ? ' from ' : ' to '];
        }
        if (activity.summary_fields.object1 && activity.summary_fields.object1.name) {
            descr += activity.summary_fields.object1.base + ' <a href=\"' + BuildUrl(activity.summary_fields.object1) + '\">'
                + activity.summary_fields.object1.name + '</a>'; 
        }
        else if (activity.object1) { 
            descr += activity.object1;
        }
        return descr;
        }
        }])

    .factory('ShowDetail', ['$rootScope', 'Rest', 'Alert', 'GenerateForm', 'ProcessErrors', 'GetBasePath', 'FormatDate', 'ActivityDetailForm',
    'Empty',
    function($rootScope, Rest, Alert, GenerateForm, ProcessErrors, GetBasePath, FormatDate, ActivityDetailForm, Empty) {
    return function(activity_id) {

        var generator = GenerateForm;
        var form = ActivityDetailForm;
        var scope;
        
        var url = GetBasePath('activity_stream') + activity_id + '/';
        
        // Retrieve detail record and prepopulate the form
        Rest.setUrl(url);
        Rest.get()
            .success( function(data, status, headers, config) {
                // load up the form
                var results = data;
                $rootScope.flashMessage = null;

                $('#form-modal').on('show.bs.modal', function (e) {
                    $('#form-modal-body').css({
                        width:'auto',  //probably not needed
                        height:'auto', //probably not needed 
                        'max-height':'100%'
                        });
                    });

                //var n = results['changes'].match(/\n/g);
                //var rows = (n) ? n.length : 1;
                //rows = (rows < 1) ? 3 : 10;
                form.fields['changes'].rows = 10;
                scope = generator.inject(form, { mode: 'edit', modal: true, related: false});
                generator.reset();
                for (var fld in form.fields) {
                    if (results[fld]) {
                       if (fld == 'timestamp') {
                          scope[fld] = FormatDate(new Date(results[fld]));
                       }
                       else {
                          scope[fld] = results[fld];
                       }
                    }
                }
                if (results.summary_fields.object1) {
                    scope['object1_name'] = results.summary_fields.object1.name; 
                }
                if (results.summary_fields.object2) {
                    scope['object2_name'] = results.summary_fields.object2.name; 
                }
                scope['user'] = (results.summary_fields.user) ? results.summary_fields.user.username : 'system';
                scope['changes'] = JSON.stringify(results['changes'], null, '\t');                
                scope.formModalAction = function() {
                    $('#form-modal').modal("hide");
                    }
                scope.formModalActionLabel = 'OK';
                scope.formModalCancelShow = false;
                scope.formModalInfo = false;
                //scope.formModalHeader = results.summary_fields.project.name + '<span class="subtitle"> - SCM Status</span>';
                $('#form-modal .btn-success').removeClass('btn-success').addClass('btn-none');
                $('#form-modal').addClass('skinny-modal');
                if (!scope.$$phase) {
                   scope.$digest();
                }
                })
            .error( function(data, status, headers, config) {
                $('#form-modal').modal("hide");
                ProcessErrors(scope, data, status, form,
                    { hdr: 'Error!', msg: 'Failed to retrieve activity: ' + activity_id + '. GET status: ' + status });
                });
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
               defaultUrl += '?object1=' + type + '&object1_id=' + paths[paths.length - 1];
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
            ShowDetail(id);
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
                scope['activities'][i].user = (scope['activities'][i].summary_fields.user) ? scope['activities'][i].summary_fields.user.username :
                    'system';
                if (scope['activities'][i].user !== 'system') {
                    // turn user into a link when not 'system'
                    scope['activities'][i].user = "<a href=\"" + FixUrl(scope['activities'][i].related.user) + "\">" + 
                        scope['activities'][i].user + "</a>";
                }
                
                // Objects
                var href;
                var deleted = /^\_delete/;
                if (scope['activities'][i].summary_fields.object1 && scope['activities'][i].summary_fields.object1.name) {
                    if ( !deleted.test(scope['activities'][i].summary_fields.object1.name) ) {
                        href = BuildUrl(scope['activities'][i].summary_fields.object1);
                        scope['activities'][i].objects = "<a href=\"" + href + "\">" + scope['activities'][i].summary_fields.object1.name + "</a>";
                    }
                    else {
                        scope['activities'][i].objects = scope['activities'][i].summary_fields.object1.name;
                    }
                }
                else if (scope['activities'][i].object1) {
                    scope['activities'][i].objects = scope['activities'][i].object1;
                }
                if (scope['activities'][i].summary_fields.object2 && scope['activities'][i].summary_fields.object2.name) {
                    if ( !deleted.test(scope['activities'][i].summary_fields.object2.name) ) {
                        href = BuildUrl(scope['activities'][i].summary_fields.object2);
                        scope['activities'][i].objects += ", <a href=\"" + href + "\">" + scope['activities'][i].summary_fields.object2.name + "</a>";
                    }
                    else {
                        scope['activities'][i].objects += "," + scope['activities'][i].summary_fields.object2.name;
                    }
                }
                else if (scope['activities'][i].object2) {
                    scope['activities'][i].objects += ", " + scope['activities'][i].object1;
                }

                // Description
                scope['activities'][i].description = BuildDescription(scope['activities'][i]);

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
    