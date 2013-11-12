/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  SearchHelper
 *
 *  All the parts for controlling the search widget on 
 *  related collections.
 *
 *  SearchInit({
 *      scope:       <scope>,
 *      set:         <model name (i.e. organizations) used in ng-repeat>
 *      url:         <default api url used to load data>
 *      list:        <list object used by ListGenerator>
 *      });   
 *
 */

angular.module('SearchHelper', ['RestServices', 'Utilities', 'RefreshHelper'])  
    .factory('SearchInit', ['Alert', 'Rest', 'Refresh', '$location', function(Alert, Rest, Refresh, $location) {
    return function(params) {
        
        var scope = params.scope;
        var set = params.set;
        var defaultUrl = params.url;
        var list = params.list; 
        var iterator = (params.iterator) ? params.iterator : list.iterator;
        var sort_order; 
        
        function setDefaults() {
            // Set default values
            for (fld in list.fields) {
                if (list.fields[fld].key) {
                   if (list.fields[fld].sourceModel) {
                      var fka = list.fields[fld].sourceModel + '__' + list.fields[fld].sourceField;
                      sort_order = (list.fields[fld].desc) ? '-' + fka : fka;
                   }
                   else {
                      sort_order = (list.fields[fld].desc) ? '-' + fld : fld; 
                   }
                   if (list.fields[fld].searchable == undefined || list.fields[fld].searchable == true) {
                      scope[iterator + 'SearchField'] = fld;
                      scope[iterator + 'SearchFieldLabel'] = list.fields[fld].label;
                   }
                   break;
                }
            }

            if (!scope[iterator + 'SearchField']) {
               // A field marked as key may not be 'searchable'
               for (fld in list.fields) {
                   if (list.fields[fld].searchable == undefined || list.fields[fld].searchable == true) { 
                      scope[iterator + 'SearchField'] = fld;
                      scope[iterator + 'SearchFieldLabel'] = list.fields[fld].label;
                      break;
                   }
               }
            }

            scope[iterator + 'SearchType'] = 'icontains';
            scope[iterator + 'SearchTypeLabel'] = 'Contains';
            scope[iterator + 'SearchParams'] = '';
            scope[iterator + 'SearchValue'] = '';
            scope[iterator + 'SelectShow'] = false;   // show/hide the Select
            scope[iterator + 'HideSearchType'] = false;
            scope[iterator + 'InputDisable'] = false;
            scope[iterator + 'ExtraParms'] = '';

            var f = scope[iterator + 'SearchField']
            if (list.fields[f].searchType && ( list.fields[f].searchType == 'boolean' 
                   || list.fields[f].searchType == 'select')) {
               scope[iterator + 'SelectShow'] = true;
               scope[iterator + 'SearchSelectOpts'] = list.fields[f].searchOptions;
            }
            if (list.fields[f].searchType && list.fields[f].searchType == 'int') {
               scope[iterator + 'HideSearchType'] = true;   
            }
            if (list.fields[f].searchType && list.fields[f].searchType == 'gtzero') {
                  scope[iterator + "InputHide"] = true;
            }
            }

        setDefaults();
       
        // Functions to handle search widget changes
        scope.setSearchField = function(iterator, fld, label) {
           scope[iterator + 'SearchFieldLabel'] = label;
           scope[iterator + 'SearchField'] = fld;
           scope[iterator + 'SearchValue'] = '';
           scope[iterator + 'SelectShow'] = false;
           scope[iterator + 'HideSearchType'] = false;
           scope[iterator + 'InputHide'] = false;
           scope[iterator + 'InputDisable'] = false;
           scope[iterator + 'SearchType'] = 'icontains';
           
           if (list.fields[fld].searchType && list.fields[fld].searchType == 'gtzero') {
              scope[iterator + "InputDisable"] = true;
           }
           else if (list.fields[fld].searchSingleValue){
              // Query a specific attribute for one specific value
              // searchSingleValue: true
              // searchType: 'boolean|int|etc.'
              // searchValue: < value to match for boolean use 'true'|'false' >
              scope[iterator + 'InputDisable'] = true;
              scope[iterator + "SearchValue"] = list.fields[fld].searchValue;
              // For boolean type, SearchValue must be an object
              if (list.fields[fld].searchType == 'boolean' && list.fields[fld].searchValue == 'true') {
                 scope[iterator + "SearchSelectValue"] = { value: 1 }; 
              }
              else if (list.fields[fld].searchType == 'boolean' && list.fields[fld].searchValue == 'false') {
                 scope[iterator + "SearchSelectValue"] = { value: 0 };
              }
              else {
                 scope[iterator + "SearchSelectValue"] = { value: list.fields[fld].searchValue };
              }
           }
           else if (list.fields[fld].searchType == 'in') {
              scope[iterator + "SearchType"] = 'in';
              scope[iterator + "SearchValue"] = list.fields[fld].searchValue;
              scope[iterator + "InputDisable"] = true;
           }
           else if (list.fields[fld].searchType && (list.fields[fld].searchType == 'boolean' 
                || list.fields[fld].searchType == 'select')) {
              scope[iterator + 'SelectShow'] = true;
              scope[iterator + 'SearchSelectOpts'] = list.fields[fld].searchOptions;
           }
           else if (list.fields[fld].searchType && list.fields[fld].searchType == 'int') {
              scope[iterator + 'HideSearchType'] = true;   
           }    
           scope.search(iterator);
           }

        scope.resetSearch = function(iterator) {
           // Respdond to click of reset button
           setDefaults();
           // Force removal of search keys from the URL
           window.location = '/#' + $location.path();
           }

        scope.setSearchType = function(iterator, type, label) {
           scope[iterator + 'SearchTypeLabel'] = label; 
           scope[iterator + 'SearchType'] = type;
           scope.search(iterator);
           }

        scope.search = function(iterator, page, load, spin) {
           // Page is optional. Added to accomodate back function on Job Events detail. 
           // Spin optional -set to false if spin not desired.
           // Load optional -set to false if loading message not desired

           scope[iterator + 'SearchSpin'] = (spin == undefined || spin == true) ? true : false;
           scope[iterator + 'Loading'] = (load == undefined || load == true) ? true : false;
           scope[iterator + 'SearchParms'] = '';
           var url = defaultUrl;
           
           if ( (scope[iterator + 'SelectShow'] == false && scope[iterator + 'SearchValue'] != '' && scope[iterator + 'SearchValue'] != undefined) ||
                (scope[iterator + 'SelectShow'] && scope[iterator + 'SearchSelectValue']) || 
                (list.fields[scope[iterator + 'SearchField']].searchType && list.fields[scope[iterator + 'SearchField']].searchType == 'gtzero') ) {
              
              if (list.fields[scope[iterator + 'SearchField']].searchField) {
                 scope[iterator + 'SearchParams'] = list.fields[scope[iterator + 'SearchField']].searchField + '__'; 
              }
              else if (list.fields[scope[iterator + 'SearchField']].sourceModel) {
                 // handle fields whose source is a related model e.g. inventories.organization
                 scope[iterator + 'SearchParams'] = list.fields[scope[iterator + 'SearchField']].sourceModel + '__' + 
                 list.fields[scope[iterator + 'SearchField']].sourceField + '__';
              }
              else if ( (list.fields[scope[iterator + 'SearchField']].searchType == 'select') && 
                        (scope[iterator + 'SearchSelectValue'].value == '' || 
                            scope[iterator + 'SearchSelectValue'].value == null) ) {
                 scope[iterator + 'SearchParams'] = scope[iterator + 'SearchField'];
              }
              else {
                 scope[iterator + 'SearchParams'] = scope[iterator + 'SearchField'] + '__'; 
              }
              
              if ( list.fields[scope[iterator + 'SearchField']].searchType && 
                   (list.fields[scope[iterator + 'SearchField']].searchType == 'int' || 
                    list.fields[scope[iterator + 'SearchField']].searchType == 'boolean' ) ) {
                 scope[iterator + 'SearchParams'] += 'int=';  
              }
              else if ( list.fields[scope[iterator + 'SearchField']].searchType && 
                        list.fields[scope[iterator + 'SearchField']].searchType == 'gtzero' ) {
                 scope[iterator + 'SearchParams'] += 'gt=0'; 
              }
              else if ( (list.fields[scope[iterator + 'SearchField']].searchType == 'select') && 
                        (scope[iterator + 'SearchSelectValue'].value == '' || 
                            scope[iterator + 'SearchSelectValue'].value == null) ) {
                 scope[iterator + 'SearchParams'] += 'iexact=';
              }
              else {
                 scope[iterator + 'SearchParams'] += scope[iterator + 'SearchType'] + '='; 
              }             
              
              if ( list.fields[scope[iterator + 'SearchField']].searchType && 
                   (list.fields[scope[iterator + 'SearchField']].searchType == 'boolean' 
                       || list.fields[scope[iterator + 'SearchField']].searchType == 'select') ) { 
                 scope[iterator + 'SearchParams'] += scope[iterator + 'SearchSelectValue'].value;
              }
              else {
                //if ( list.fields[scope[iterator + 'SearchField']].searchType == undefined || 
                //        list.fields[scope[iterator + 'SearchField']].searchType == 'gtzero' ) {
                 scope[iterator + 'SearchParams'] += escape(scope[iterator + 'SearchValue']);
              }
              scope[iterator + 'SearchParams'] += (sort_order) ? '&order_by=' + escape(sort_order) : '';
           }
           else {
              scope[iterator + 'SearchParams'] = (sort_order) ? 'order_by=' + escape(sort_order) : "";
           }

           if ( (iterator == 'inventory' && scope.inventoryFailureFilter) ||
                (iterator == 'host' && scope.hostFailureFilter) ) {
              scope[iterator + 'SearchParams'] += '&has_active_failures=true';
           }
           
           scope[iterator + 'Page'] = (page) ? parseInt(page) - 1 : 0;
           if (/\/$/.test(url)) {
              url += '?' + scope[iterator + 'SearchParams'];
           }
           else {
              url += '&' + scope[iterator + 'SearchParams'];
           }
           url = url.replace(/\&\&/,'&');
           url += (scope[iterator + 'PageSize']) ? '&page_size=' + scope[iterator + 'PageSize'] : "";
           if (page) {
              url += '&page=' + page;
           }
           if (scope[iterator + 'ExtraParms']) {
              url += scope[iterator + 'ExtraParms'];
           }
           Refresh({ scope: scope, set: set, iterator: iterator, url: url });
           }

        scope.sort = function(fld) {
            // reset sort icons back to 'icon-sort' on all columns
            // except the one clicked
            $('.list-header').each(function(index) {
                if ($(this).attr('id') != fld + '-header') {
                   var icon = $(this).find('i');
                   icon.attr('class','icon-sort');
                }
                });
 
            // Toggle the icon for the clicked column
            // and set the sort direction  
            var icon = $('#' + fld + '-header i');
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
            if (list.fields[fld].searchField) {
               sort_order = direction + list.fields[fld].searchField;
            }
            else if (list.fields[fld].sortField) {
               sort_order = direction + list.fields[fld].sortField;
            }
            else {
               if (list.fields[fld].sourceModel) {
                  sort_order = direction + list.fields[fld].sourceModel + '__' + list.fields[fld].sourceField;
               }
               else {
                  sort_order = direction + fld; 
               }
            }
            scope.search(list.iterator);
            }

        }
        }]);
