/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *
 *  JobEvents.js
 *  
 *  Controller functions for the Job Events model.
 *
 */

'use strict';

function JobEventsList ($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, JobEventList,
                        GenerateList, LoadBreadCrumbs, Prompt, SearchInit, PaginateInit, ReturnToCaller,
                        ClearScope, ProcessErrors, GetBasePath, LookUpInit, ToggleChildren,
                        FormatDate, EventView)
{
    ClearScope('htmlTemplate');
    var list = JobEventList;
    list.base = $location.path();
    
    var defaultUrl = GetBasePath('jobs') + $routeParams.id  + '/job_events/'; //?parent__isnull=1';
    
    var view = GenerateList;
    var base = $location.path().replace(/^\//,'').split('/')[0];
    var scope = view.inject(list, { mode: 'edit' });

    scope.job_id = $routeParams.id;
    $rootScope.flashMessage = null;
    scope.selected = [];
    scope.expand = true;    //on load, automatically expand all nodes

    scope.parentNode = 'parent-event';  // used in ngClass to dynamicall set row level class and control
    scope.childNode = 'child-event';    // link color and cursor

    function formatJSON(eventData) {
        //turn JSON event data into an html form
        var html = '';
        if (eventData['res']) {
           var n, rows;
           var found =  false;
           if (typeof eventData.res == 'string') {
              n = eventData['res'].match(/\n/g);
              rows = (n) ? n.length : 1;
              rows = (rows > 10) ? 10 : rows;
              found = true;
              html += "<div class=\"form-group\">\n";
              html += "<label>Traceback:</label>\n";
              html += "<textarea readonly class=\"form-control nowrap\" rows=\"" + rows + "\">" + eventData.res + "</textarea>\n";
              html += "</div>\n";
           }
           else {
              for (var fld in eventData.res) {
                  if ( (fld == 'msg' || fld == 'stdout' || fld == 'stderr') && 
                       (eventData.res[fld] !== null && eventData.res[fld] !== '') ) {
                       html += "<div class=\"form-group\">\n";
                       html += "<label>"; 
                       switch(fld) {
                          case 'msg':
                          case 'stdout':
                             html += 'Output:';
                             break;
                          case 'stderr':
                             html += 'Error:';
                             break;
                       }
                       html += "</label>\n";
                       n = eventData['res'][fld].match(/\n/g);
                       rows = (n) ? n.length : 1;
                       rows = (rows > 10) ? 10 : rows;
                       html += "<textarea readonly class=\"form-control nowrap\" rows=\"" + rows + "\">" + eventData.res[fld] + "</textarea>\n";
                       html += "</div>\n";
                       found = true;
                  }
                  if ( fld == "results" && Array.isArray(eventData.res[fld]) && eventData.res[fld].length > 0 ) {
                     //html += "<textarea readonly class="
                     var txt = '';
                     for (var i=0; i < eventData.res[fld].length; i++) {
                         txt += eventData.res[fld][i];
                     }
                     n = txt.match(/\n/g);
                     rows = (n) ? n.length : 1;
                     rows = (rows > 10) ? 10 : rows;
                     if (txt !== '') {
                        html += "<div class=\"form-group\">\n";
                        html += "<label>Results:</label>\n";
                        html += "<textarea readonly class=\"form-control nowrap\" rows=\"" + rows + "\">" + txt + "</textarea>\n";
                        html += "</div>\n";
                        found = true;
                     }
                  } 
                  if (fld == "rc" && eventData.res[fld] != '') {
                     html += "<div class=\"form-group\">\n";
                     html += "<label>Return Code:</label>\n";
                     html += "<input type=\"text\" class=\"form-control\" value=\"" + eventData.res[fld] + "\" readonly >\n";
                     html += "</div>\n";
                     found = true;
                  }
              }
           }
           html = (found) ? "<form class=\"event-form\">\n" + html + "</form>\n" : '';
        }
        if (eventData['host']) {
           html = "<span class=\"event-detail-host visible-sm\">" + eventData['host'] + "</span>\n" + html;
        }
        else {
           html = (html == '' ) ? null : html;
        }
        return html;
        }

    if (scope.PostRefreshRemove) {
       scope.PostRefreshRemove();
    }
    scope.PostRefreshRemove = scope.$on('PostRefresh', function() {
        // Initialize the parent levels
        var set = scope[list.name];
        var cDate;
        for (var i=0; i < set.length; i++) {
            set[i].event_display = set[i].event_display.replace(/^\u00a0*/g,'');
            if (set[i].event_level < 3 ) {
               set[i]['ngclick'] = "toggleChildren(" + set[i].id + ", \"" + set[i].related.children + "\")";
               set[i]['ngicon'] = 'icon-collapse-alt';
               set[i]['class'] = 'parentNode';
            }
            else {
               set[i]['class'] = 'childNode';
               set[i]['event_detail'] = formatJSON(set[i].event_data);
            }
            set[i]['show'] = true;
            set[i]['spaces'] = set[i].event_level * 24;
            if (scope.jobevents[i].failed) {
               scope.jobevents[i].status = 'error';
               if (i == set.length - 1) {
                  scope.jobevents[i].statusBadgeToolTip = "A failure occurred durring one or more playbook tasks.";
               }
               else if (set[i].event_level < 3) {
                  scope.jobevents[i].statusBadgeToolTip = "A failure occurred within the children of this event.";
               }
               else {
                  scope.jobevents[i].statusBadgeToolTip = "A failure occurred. Click to view details";
               }
            }
            else if (scope.jobevents[i].changed) {
               scope.jobevents[i].status = 'changed';
               if (i == set.length - 1) {
                  scope.jobevents[i].statusBadgeToolTip = "A change was completed durring one or more playbook tasks.";
               }
               else if (set[i].event_level < 3) {
                  scope.jobevents[i].statusBadgeToolTip = "A change was completed by one or more children of this event.";
               }
               else {
                  scope.jobevents[i].statusBadgeToolTip = "A change was completed. Click to view details";
               }
            }
            else {
               scope.jobevents[i].status = 'success';
               if (i == set.length - 1) {
                  scope.jobevents[i].statusBadgeToolTip = "All playbook tasks completed successfully.";
               }
               else if (set[i].event_level < 3) {
                  scope.jobevents[i].statusBadgeToolTip = "All the children of this event completed successfully.";
               }
               else {
                  scope.jobevents[i].statusBadgeToolTip = "No errors occurred. Click to view details";
               }
            }
            cDate = new Date(set[i].created);
            set[i].created = FormatDate(cDate);
        }

        // need job_status so we can show/hide refresh button
        Rest.setUrl(GetBasePath('jobs') + scope.job_id);
        Rest.get()
            .success( function(data, status, headers, config) {
                scope.job_status = data.status;
                scope.job_name = data.summary_fields.job_template.name;
                LoadBreadCrumbs({ path: '/jobs/' + scope.job_id, title: scope.job_name });
                if (!(data.status == 'pending' || data.status == 'waiting' || data.status == 'running')) {
                   if ($rootScope.timer) {
                      clearInterval($rootScope.timer);
                   }
                }
                })
            .error(  function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                  { hdr: 'Error!', msg: 'Failed to get job status for job: ' + scope.job_id + '. GET status: ' + status });
                });
        });

    SearchInit({ scope: scope, set: 'jobevents', list: list, url: defaultUrl });
    
    var page = ($routeParams.page) ? parseInt($routeParams.page) - 1 : null;
    PaginateInit({ scope: scope, list: list, url: defaultUrl, page: page });

    // Called from Inventories tab, host failed events link:
    if ($routeParams.host) {
       scope[list.iterator + 'SearchField'] = 'host'; 
       scope[list.iterator + 'SearchValue'] = $routeParams.host;
       scope[list.iterator + 'SearchFieldLabel'] = list.fields['host'].label;
    }
    
    scope.search(list.iterator, $routeParams.page);
    
    scope.toggleChildren = function(id, children) {
        ToggleChildren({
            scope: scope, 
            list: list,
            id: id,
            children: children
            });
        }
    
    scope.viewJobEvent = function(id) {
       EventView({ event_id: id });
       }

    scope.refresh = function() {
       scope['jobSearchSpin'] = true;
       scope['jobLoading'] = true;
       Refresh({ scope: scope, set: 'jobevents', iterator: 'jobevent', url: scope['current_url'] });
       }
}

JobEventsList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'JobEventList',
                           'GenerateList', 'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope',
                           'ProcessErrors','GetBasePath', 'LookUpInit', 'ToggleChildren', 'FormatDate', 'EventView'
                           ];

function JobEventsEdit ($scope, $rootScope, $compile, $location, $log, $routeParams, JobEventForm, GenerateForm,
                        Rest, Alert, ProcessErrors, LoadBreadCrumbs, ClearScope, GetBasePath, FormatDate, EventView) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.
   // Inject dynamic view
   var form = JobEventForm;
   var generator = GenerateForm;
   var scope = GenerateForm.inject(form, {mode: 'edit', related: true});
   generator.reset();
   
   var defaultUrl = GetBasePath('base') + 'job_events/' + $routeParams.event_id + '/';
   var base = $location.path().replace(/^\//,'').split('/')[0];
   
   // Retrieve detail record and prepopulate the form
   Rest.setUrl(defaultUrl); 
   Rest.get()
       .success( function(data, status, headers, config) {
          scope['event_display'] = data['event_display'].replace(/^\u00a0*/g,'');
          LoadBreadCrumbs({ path: '/jobs/' + $routeParams.job_id + '/job_events/' + $routeParams.event_id,
                title: scope['event_display'] });
          for (var fld in form.fields) {
              switch(fld) {
                  case 'status':
                     if (data['failed']) {
                        scope['status'] = 'error';
                     }
                     else if (data['changed']) {
                        scope['status'] = 'changed';
                     }
                     else {
                        scope['status'] = 'success';
                     }
                     break;
                  case 'created':
                     var cDate = new Date(data['created']);
                     scope['created'] = FormatDate(cDate);
                     break;
                  case 'host':
                     if (data['summary_fields'] && data['summary_fields']['host']) {
                        scope['host'] = data['summary_fields']['host']['name'];
                     }
                     break;
                  case 'id':
                  case 'task':
                  case 'play':
                     scope[fld] = data[fld];
                     break;
                  case 'start':
                  case 'end':
                    if (data['event_data'] && data['event_data']['res'] && data['event_data']['res'][fld] !== undefined) {
                       var cDate = new Date(data['event_data']['res'][fld]);
                       scope[fld] = FormatDate(cDate);
                    }
                    break;
                  case 'msg':
                  case 'stdout':
                  case 'stderr':
                  case 'delta':
                  case 'rc':
                     if (data['event_data'] && data['event_data']['res'] && data['event_data']['res'][fld] !== undefined) {
                        scope[fld] = data['event_data']['res'][fld];
                        if (form.fields[fld].type == 'textarea') {
                           var n = data['event_data']['res'][fld].match(/\n/g);
                           var rows = (n) ? n.length : 1;
                           rows = (rows > 15) ? 5 : rows;
                           $('textarea[name="' + fld + '"]').attr('rows',rows);
                        }
                      }
                     break;
                  case 'module_name':
                  case 'module_args':
                     if (data['event_data']['res'] && data['event_data']['res']['invocation']) {
                        scope[fld] = data['event_data']['res']['invocation'][fld];
                     }
                     break;
              }
          }
          })
      .error( function(data, status, headers, config) {
          ProcessErrors(scope, data, status, null,
              { hdr: 'Error!', msg: 'Failed to retrieve host: ' + $routeParams.event_id + '. GET status: ' + status });
          });

      scope.navigateBack = function() {
          var url = '/jobs/' + $routeParams.job_id + '/job_events';
          if ($routeParams.page) {
             url += '?page=' + $routeParams.page;
          }
          $location.url(url);
          }

      scope.rawView = function() {
          EventView({"event_id": scope.id });
          }
   
}

JobEventsEdit.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'JobEventForm', 
                          'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ClearScope', 'GetBasePath',
                          'FormatDate', 'EventView'
                          ];
