/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  RelatedSearchHelper
 *
 *  All the parts for controlling the search widget on 
 *  related collections.
 *
 *  SearchInit({
 *      scope: <scope>,
 *      relatedSets: <array of related collections {model_name, url, iterator}>,
 *      form: <form object used by FormGenerator>
 *      });   
 *
 *
 */

angular.module('RelatedSearchHelper', ['RestServices', 'Utilities','RefreshRelatedHelper'])  
    .factory('RelatedSearchInit', ['Alert', 'Rest', 'RefreshRelated', function(Alert, Rest, RefreshRelated) {
    return function(params) {
        
        var scope = params.scope;
        var relatedSets = params.relatedSets;
        var form = params.form; 
        
        // Set default values
        var iterator, f;
        for (var set in form.related) {
            if (form.related[set].type != 'tree') {
                iterator = form.related[set].iterator;
                for (var fld in form.related[set].fields) {
                    if (form.related[set].fields[fld].key) {
                       scope[iterator + 'SearchField'] = fld
                       scope[iterator + 'SearchFieldLabel'] = form.related[set].fields[fld].label;
                       break;
                    }
                }
                scope[iterator + 'SortOrder'] = null;
                scope[iterator + 'SearchType'] = 'contains';
                scope[iterator + 'SearchTypeLabel'] = 'Contains';
                scope[iterator + 'SelectShow'] = false;
                scope[iterator + 'HideSearchType'] = false;
                f = scope[iterator + 'SearchField']
                if (form.related[set].fields[f].searchType && ( form.related[set].fields[f].searchType == 'boolean' 
                      || form.related[set].fields[f].searchType == 'select')) {
                   scope[iterator + 'SelectShow'] = true;
                   scope[iterator + 'SearchSelectOpts'] = list.fields[f].searchOptions;
                }
                if (form.related[set].fields[f].searchType && form.related[set].fields[f].searchType == 'int') {
                   scope[iterator + 'HideSearchType'] = true;   
                }
                if (form.related[set].fields[f].searchType && form.related[set].fields[f].searchType == 'gtzero') {
                      scope[iterator + "InputHide"] = true;
                }
            }
        } 
        
        // Functions to handle search widget changes
        scope.setSearchField = function(iterator, fld, label) {
           
           for (var related in form.related) {
               if ( form.related[related].iterator == iterator ) {
                  var f = form.related[related].fields[fld];
               }
           }
           
           scope[iterator + 'SearchFieldLabel'] = label;
           scope[iterator + 'SearchField'] = fld;
           scope[iterator + 'SearchValue'] = '';
           scope[iterator + 'SelectShow'] = false;
           scope[iterator + 'HideSearchType'] = false;
           scope[iterator + 'InputHide'] = false;

           if (f.searchType !== undefined && f.searchType == 'gtzero') {
              scope[iterator + "InputHide"] = true;
           }
           if (f.searchType !== undefined && (f.searchType == 'boolean' 
                || f.searchType == 'select')) {
              scope[iterator + 'SelectShow'] = true;
              scope[iterator + 'SearchSelectOpts'] = f.searchOptions;
           }
           if (f.searchType !== undefined && f.searchType == 'int') {
              scope[iterator + 'HideSearchType'] = true;   
           }

           if (iterator == 'host') {
              if (fld == 'has_active_failures') {
                 scope['hostFailureFilter'] = true;
              }
              else {
                 scope['hostFailureFilter'] = false;
              }
           }

           scope.search(iterator);

           }

        scope.setSearchType = function(model, type, label) {
           scope[model + 'SearchTypeLabel'] = label; 
           scope[model + 'SearchType'] = type;
           scope.search(model);
           }

        scope.search = function(iterator) {
           scope[iterator + 'SearchSpin'] = true;
           scope[iterator + 'Loading'] = true;

           if (iterator == 'host') {
              if (scope['hostSearchField'] == 'has_active_failures') {
                 if (scope['hostSearchSelectValue'] && scope['hostSearchSelectValue'].value == 1) {
                    scope['hostFailureFilter'] = true;
                 }
                 else {
                    scope['hostFailureFilter'] = false;
                 }
              }
           }

           var set, url, iterator, sort_order;
           for (var key in relatedSets) {
               if (relatedSets[key].iterator == iterator) {
                  set = key;
                  url = relatedSets[key].url;
                  for (var fld in form.related[key].fields) {
                      if (form.related[key].fields[fld].key) {
                         if (form.related[key].fields[fld].desc) {
                            sort_order = '-' + fld;
                         }
                         else {
                            sort_order = fld;
                         }
                      }
                  }
                  break;
               }
           }

           sort_order = (scope[iterator + 'SortOrder'] == null) ? sort_order : scope[iterator + 'SortOrder'];

           var f = form.related[set].fields[scope[iterator + 'SearchField']];
           if ( (scope[iterator + 'SelectShow'] == false && scope[iterator + 'SearchValue'] != '' && scope[iterator + 'SearchValue'] != undefined) ||
                (scope[iterator + 'SelectShow'] && scope[iterator + 'SearchSelectValue']) || (f.searchType && f.searchType == 'gtzero') ) {
              if (f.sourceModel) {
                 // handle fields whose source is a related model e.g. inventories.organization
                 scope[iterator + 'SearchParams'] = '?' + f.sourceModel + '__' + f.sourceField + '__';
              }
              else if (f.searchField) {
                 scope[iterator + 'SearchParams'] = '?' + f.searchField + '__'; 
              }
              else {
                 scope[iterator + 'SearchParams'] = '?' + scope[iterator + 'SearchField'] + '__'; 
              }
              
              if ( f.searchType && (f.searchType == 'int' || f.searchType == 'boolean' ) ) {
                 scope[iterator + 'SearchParams'] += 'int=';  
              }
              else if ( f.searchType && f.searchType == 'gtzero' ) {
                 scope[iterator + 'SearchParams'] += 'gt=0'; 
              }
              else {
                 scope[iterator + 'SearchParams'] += scope[iterator + 'SearchType'] + '='; 
              }             
              
              if ( f.searchType && (f.searchType == 'boolean' || f.searchType == 'select') ) { 
                   scope[iterator + 'SearchParams'] += scope[iterator + 'SearchSelectValue'].value;
              }
              else if ( f.searchType == undefined || f.searchType == 'gtzero' ) {
                 scope[iterator + 'SearchParams'] += escape(scope[iterator + 'SearchValue']);
              }
              scope[iterator + 'SearchParams'] += (sort_order) ? '&order_by=' + escape(sort_order) : '';
           }
           else {
              scope[iterator + 'SearchParams'] = ''; 
              scope[iterator + 'SearchParams'] += (sort_order) ? '?order_by=' + escape(sort_order) : '';
           }

           scope[iterator + 'Page'] = 0;
           url += scope[iterator + 'SearchParams'];
           url += (scope[iterator + 'PageSize']) ? '&page_size=' + scope[iterator + 'PageSize'] : "";
           RefreshRelated({ scope: scope, set: set, iterator: iterator, url: url });
           }


        scope.sort = function(iterator, fld) {
            var sort_order; 

            // reset sort icons back to 'icon-sort' on all columns
            // except the one clicked
            $('.' + iterator + ' .list-header').each(function(index) {
                if ($(this).attr('id') != iterator + '-' + fld + '-header') {
                   var icon = $(this).find('i');
                   icon.attr('class','icon-sort');
                }
                });
 
            // Toggle the icon for the clicked column
            // and set the sort direction  
            var icon = $('#' + iterator + '-' + fld + '-header i');
            var direction = '';
            if (icon.hasClass('icon-sort')) {
               icon.removeClass('icon-sort');
               icon.addClass('icon-sort-up');
            }
            else if (icon.hasClass('icon-sort-up')) {
               icon.removeClass('icon-sort-up');
               icon.addClass('icon-sort-down');
               direction = '-';
            }
            else if (icon.hasClass('icon-sort-down')) {
               icon.removeClass('icon-sort-down');
               icon.addClass('icon-sort-up');
            }

            // Set the sorder order value and call the API to refresh the list with the new order
            for (var set in form.related) {
                if (form.related[set].iterator == iterator) {
                   if (form.related[set].fields[fld].sourceModel) {
                      sort_order = direction + form.related[set].fields[fld].sourceModel + '__' + 
                          form.related[set].fields[fld].sourceField;
                   }
                   else {
                     sort_order = direction + fld; 
                   }
                }
            }
            scope[iterator + 'SortOrder'] = sort_order;
            scope.search(iterator);
            }
        }
        }]);
