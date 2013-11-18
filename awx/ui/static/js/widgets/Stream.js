/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Stream.js 
 *
 *  Activity stream widget that can be called from anywhere
 *
 */

angular.module('StreamWidget', ['RestServices', 'Utilities', 'StreamListDefinition', 'SearchHelper', 'PaginateHelper',
        'RefreshHelper', 'ListGenerator', 'StreamWidget'])
    
    .factory('ShowStream', [ function() {
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
        
        // Try not to overlap footer. Because stream is positioned absolute, the parent
        // doesn't resize correctly when stream is loaded.
        $('#tab-content-container').css({ 'min-height': stream.height() + 50 });

        // Slide in stream
        stream.show('slide', {'direction': 'left'}, {'duration': 500, 'queue': false });
        
        }
        }])

    .factory('HideStream', [ function() {
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
        if (activity.summary_fields.user) {
            // this is a user transaction
            var usr = FixUrl(activity.related.user);
            descr += 'User <a href=\"' + usr + '\">' + activity.summary_fields.user.username + '</a> ';
        }
        else {
            descr += 'System '; 
        }
        descr += activity.operation;
        descr += (/e$/.test(activity.operation)) ? 'd ' : 'ed ';
        if (activity.summary_fields.object2) {
            descr += activity.summary_fields.object2.base + ' <a href=\"' + BuildUrl(activity.summary_fields.object2) + '\">'
                + activity.summary_fields.object2.name + '</a>' + [ (activity.operation == 'disassociate') ? ' from ' : ' to ']; 
        }
        if (activity.summary_fields.object1) {
            descr += activity.summary_fields.object1.base + ' <a href=\"' + BuildUrl(activity.summary_fields.object1) + '\">'
                + activity.summary_fields.object1.name + '</a>'; 
        }
        return descr;
        }
        }])

    .factory('ShowDetail', ['Rest', 'Alert', 'GenerateForm', 'ProcessErrors', 'GetBasePath', 'FormatDate', 'ActivityDetailForm',
    function(Rest, Alert, GenerateForm, ProcessErrors, GetBasePath, FormatDate, ActivityDetailForm) {
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
        'ShowDetail',
    function($rootScope, $location, Rest, GetBasePath, ProcessErrors, Wait, StreamList, SearchInit, PaginateInit, GenerateList,
        FormatDate, ShowStream, HideStream, BuildDescription, FixUrl, BuildUrl, ShowDetail) {
    return function(params) {
    
        var list = StreamList;
        var defaultUrl = GetBasePath('activity_stream');
        var view = GenerateList;
        var base = $location.path().replace(/^\//,'').split('/')[0];
       
        if (base !== 'home') {
           var type = (base == 'inventories') ? 'inventory' : base.replace(/s$/,'');
           defaultUrl += '?or__object1=' + type + '&or__object2=' + type;
        }
        
        // Push the current page onto browser histor. If user clicks back button, restore current page without 
        // stream widget
        // window.history.pushState({}, "AnsibleWorks AWX", $location.path());

        // Add a container for the stream widget
        $('#tab-content-container').append('<div id="stream-container"><div id=\"stream-content\"></div></div><!-- Stream widget -->');

        ShowStream();
        
        // Generate the list
        var scope = view.inject(list, { 
            mode: 'edit',
            id: 'stream-content', 
            breadCrumbs: true, 
            searchSize: 'col-lg-3',
            secondWidget: true
            });

        scope.closeStream = function() { 
            HideStream();
            }  

        scope.refreshStream = function() {
            scope.search(list.iterator);
            }

        scope.showDetail = function(id) {
            ShowDetail(id);
            }

        if (scope.removePostRefresh) {
            scope.removePostRefresh();    
        }
        scope.removePostRefresh = scope.$on('PostRefresh', function() {
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
                if (scope['activities'][i].summary_fields.object1) {
                    if ( !deleted.test(scope['activities'][i].summary_fields.object1.name) ) {
                        href = BuildUrl(scope['activities'][i].summary_fields.object1);
                        scope['activities'][i].objects = "<a href=\"" + href + "\">" + scope['activities'][i].summary_fields.object1.name + "</a>";
                    }
                    else {
                        scope['activities'][i].objects = scope['activities'][i].summary_fields.object1.name;
                    }
                }
                if (scope['activities'][i].summary_fields.object2) {
                    if ( !deleted.test(scope['activities'][i].summary_fields.object2.name) ) {
                        href = BuildUrl(scope['activities'][i].summary_fields.object2);
                        scope['activities'][i].objects += ", <a href=\"" + href + "\">" + scope['activities'][i].summary_fields.object2.name + "</a>";
                    }
                    else {
                        scope['activities'][i].objects += scope['activities'][i].summary_fields.object2.name;
                    }
                }
                scope['activities'][i].description = BuildDescription(scope['activities'][i]);
            }
            });

        // Initialize search and paginate pieces and load data
        SearchInit({ scope: scope, set: list.name, list: list, url: defaultUrl });
        PaginateInit({ scope: scope, list: list, url: defaultUrl });
        scope.search(list.iterator);
        
        /*
        scope.$watch(list.iterator + 'SearchField', function(newVal, oldVal) {
            console.log('newVal: ' + newVal);
            html += ""
            html += "<input id=\"search_attribute_input\" type=\"text\" ng-show=\"" + iterator + "ShowAttribute\" class=\"form-control ";
            html += "\" ng-model=\"" + iterator + "AttributeValue\" ng-change=\"search('" + iterator + 
                "')\" aw-placeholder=\"" + iterator + "AttributePlaceholder\" type=\"text\">\n";
            });*/

        }
        }]);
    