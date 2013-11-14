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
        $('#tab-content-container').css({ 'min-height': stream.height() });

        // Slide in stream
        stream.show('slide', {'direction': 'left'}, {'duration': 500, 'queue': false });
        
        }
        }])

    .factory('HideStream', [ 'ClearScope', function(ClearScope) {
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

    .factory('Stream', ['$rootScope', '$location', 'Rest', 'GetBasePath', 'ProcessErrors', 'Wait', 'StreamList', 'SearchInit', 
        'PaginateInit', 'GenerateList', 'FormatDate', 'ShowStream', 'HideStream',
    function($rootScope, $location, Rest, GetBasePath, ProcessErrors, Wait, StreamList, SearchInit, PaginateInit, GenerateList,
        FormatDate, ShowStream, HideStream) {
    return function(params) {
    
        var list = StreamList;
        var defaultUrl = GetBasePath('activity_stream');
        var view = GenerateList;
        
        // Push the current page onto browser histor. If user clicks back button, restore current page without 
        // stream widget
        // window.history.pushState({}, "AnsibleWorks AWX", $location.path());

        // Add a container for the stream widget
        $('#tab-content-container').append('<div id="stream-container"><div id=\"stream-content\"></div></div><!-- Stream widget -->');
        
        // Generate the list
        var scope = view.inject(list, { 
            mode: 'edit',
            id: 'stream-content', 
            breadCrumbs: true, 
            searchSize: 'col-lg-4'
            });

        scope.closeStream = function() { 
           HideStream();
           }  

        scope.refreshStream = function() {
           scope.search(list.iterator);
           }

        function fixUrl(u) { return u.replace(/\/api\/v1\//,'/#/'); }

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
                    'System';
                if (scope['activities'][i].user !== 'System') {
                    scope['activities'][i].userLink = (scope['activities'][i].summary_fields.user) ? fixUrl(scope['activities'][i].related.user) :
                        "";
                }

                // Objects
                var href;
                if (scope['activities'][i].summary_fields.object1) {
                    href = fixUrl(scope['activities'][i].related.object_1);
                    scope['activities'][i].objects = "<a href=\"" + href + "\">" + scope['activities'][i].summary_fields.object1.name + "</a>";
                }
                if (scope['activities'][i].summary_fields.object2) {
                    href = fixUrl(scope['activities'][i].related.object_2);
                    scope['activities'][i].objects += ", <a href=\"" + href + "\">" + scope['activities'][i].summary_fields.object2.name + "</a>";
                }
            }
            ShowStream();
            });

        // Initialize search and paginate pieces and load data
        SearchInit({ scope: scope, set: list.name, list: list, url: defaultUrl });
        PaginateInit({ scope: scope, list: list, url: defaultUrl });
        scope.search(list.iterator);
        
        }
        }]);
    