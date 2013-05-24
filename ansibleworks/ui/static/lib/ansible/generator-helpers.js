/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 * GeneratorHelpers
 *
 * Functions shared between FormGenerator and ListGenerator 
 * 
 */

angular.module('GeneratorHelpers', [])  
    .factory('SearchWidget', function() {
    return function(params) {
        //
        // Generate search widget
        //
        var iterator = params.iterator; 
        var form = params.template; 
        var useMini = params.mini; 
        var label = (params.label) ? params.label : null;
        var html= '';
   
        html += "<div class=\"search-widget\">\n";
        html += (label) ? "<label>" + label +"</label>" : "";
        html += "<div class=\"input-prepend input-append\">\n";
        html += "<div class=\"btn-group\">\n";
        html += "<button class=\"btn "; 
        html += (useMini) ? "btn-mini " : "btn-small";
        html += "dropdown-toggle\" data-toggle=\"dropdown\">\n";
        html += "<span ng-bind=\"" + iterator + "SearchFieldLabel\"></span>\n";
        html += "<span class=\"caret\"></span>\n";
        html += "</button>\n";
        html += "<ul class=\"dropdown-menu\">\n";
        
        for ( var fld in form.fields) {
          if (form.fields[fld].notSearchable == undefined || form.fields[fld].notSearchable == false) {
             html += "<li><a href=\"\" ng-click=\"setSearchField('" + iterator + "','";
             html += fld + "','" + form.fields[fld].label + "')\">" 
                 + form.fields[fld].label + "</a></li>\n";
          }
        }
        html += "</ul>\n";
        html += "</div>\n";

        html += "<select ng-show=\"" + iterator + "SelectShow\" ng-model=\""+ iterator + "SearchSelectValue\" ng-change=\"search('" + iterator + "')\" ";
        html += "ng-options=\"c.name for c in " + iterator + "SearchSelectOpts\" class=\"search-select\"></select>\n";

        html += "<input ng-hide=\"" + iterator + "SelectShow || " + iterator + "InputHide\" class=\"input-medium";
        html += (useMini) ? " field-mini-height" : "";
        html += "\" ng-model=\"" + iterator + "SearchValue\" ng-change=\"search('" + iterator + 
                "')\" placeholder=\"Search\" type=\"text\" >\n";

        html += "<div class=\"btn-group\">\n";
        html += "<button ng-hide=\"" + iterator + "SelectShow || " + iterator + "HideSearchType || " + iterator + "InputHide\" class=\"btn ";
        html += (useMini) ? "btn-mini " : "btn-small";
        html += "dropdown-toggle\" data-toggle=\"dropdown\">\n";
        html += "<span ng-bind=\"" + iterator + "SearchTypeLabel\"></span>\n";
        html += "<span class=\"caret\"></span>\n";
        html += "</button>\n";
        html += "<ul class=\"dropdown-menu\">\n";
        html += "<li><a href=\"\" ng-click=\"setSearchType('" + iterator + "','iexact','Exact Match')\">Exact Match</a></li>\n";
        html += "<li><a href=\"\" ng-click=\"setSearchType('" + iterator + "','icontains','Contains')\">Contains</a></li>\n";
        html += "</ul>\n";
        html += "</div>\n";
        html += "</div>\n";
        html += "<div class=\"spin\"><i class=\"icon-spinner icon-spin\" ng-show=\"" + iterator + "SearchSpin == true\"></i></div>\n";
        html += "</div>\n";

        return html;
        
        }
        })

    .factory('PaginateWidget', function() {
    return function(params) {
        var set = params.set; 
        var iterator = params.iterator; 
        var useMini = params.mini;
        var mode = (params.mode) ? params.mode : null;
        var html = '';

        if (mode == 'lookup') {
           html += "<div class=\"lookup-navigation";
        }
        else { 
           html += "<div class=\"footer-navigation";
        }
        html += (useMini) ? " related-footer" : "";
        html += "\">\n";
        html += "<form class=\"form-inline\">\n";
        html += "<button class=\"previous btn";
        html += (useMini) ? " btn-mini\" " : "\" ";
        html += "ng-click=\"prevSet('" + set + "','" + iterator + "')\" " +
                "ng-disabled=\"" + iterator + "PrevUrl == null || " + iterator + "PrevUrl == undefined\"><i class=\"icon-chevron-left\"></i> Prev</button>\n";
        html += "<button class=\"next btn btn";
        html += (useMini) ? " btn-mini\" " : "\" ";
        html += " ng-click=\"nextSet('" + set + "','" + iterator + "')\"" + 
                "ng-disabled=\"" + iterator + "NextUrl == null || " + iterator + "NextUrl == undefined\">Next <i class=\"icon-chevron-right\"></i></button>\n";
        
        if (mode != 'lookup') {
           html += "<label class=\"page-size-label\">Rows per page:</label>\n";
           html += "<select ng-model=\"" + iterator + "PageSize\" ng-change=\"changePageSize('" + 
                    set + "'," + "'" + iterator + "')\" class=\"input-mini";
           html += (useMini) ? " field-mini-height" : "";
           html += " page-size\">\n";
           html += "<option value=\"10\" selected>10</option>\n";
           html += "<option value=\"20\" selected>20</option>\n";
           html += "<option value=\"40\">40</option>\n";
           html += "<option value=\"60\">60</option>\n";
           html += "<option value=\"80\">80</option>\n";    
           html += "</select>\n";
        }

        html += "<div class=\"page-number-small\"";
        html += ">Page: {{ " + iterator + "Page + 1 }} of {{ " + iterator + "PageCount }}</div>\n";
        html += "</form>\n";
        html += "</div>\n";

        return html;

        }
        });