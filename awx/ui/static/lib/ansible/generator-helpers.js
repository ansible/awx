/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 * GeneratorHelpers
 *
 * Functions shared between FormGenerator and ListGenerator 
 * 
 */

angular.module('GeneratorHelpers', ['GeneratorHelpers'])
    
    .factory('Attr', function() {
    return function(obj, key, fld) { 
        var result;
        var value = (typeof obj[key] === "string") ? obj[key].replace(/[\'\"]/g, '&quot;') : obj[key];
        switch(key) {
            case 'ngClick':
               result = "ng-click=\"" + value + "\" ";
               break;
            case 'ngOptions':
               result = "ng-options=\"" + value + "\" ";
               break;
            case 'ngClass':
                result = "ng-class=\"" + value + "\" ";
                break;
            case 'ngChange':
               result = "ng-change=\"" + value + "\" ";
               break;
            case 'ngDisabled':
                result = "ng-disabled=\"" + value + "\" ";
                break;
            case 'ngShow':
               result = "ng-show=\"" + value + "\" ";
               break;
            case 'ngHide':
               result = "ng-hide=\"" + value + "\" ";
               break;
            case 'ngBind':
                result = "ng-bind=\"" + value + "\" ";
                break;
            case 'trueValue':
               result = "ng-true-value=\"" + value + "\" ";
               break;
            case 'falseValue':
               result = "ng-false-value=\"" + value + "\" ";
               break;
            case 'awToolTip':
               result = "aw-tool-tip=\"" + value + "\" ";
               break;
            case 'awPopOver':
               // construct the entire help link
               result = "<a id=\"awp-" + fld + "\" href=\"\" aw-pop-over=\'" + value + "\' ";
               result += (obj.dataTitle) ? "data-title=\"" + obj['dataTitle'].replace(/[\'\"]/g, '&quot;') + "\" " : "";
               result += (obj.dataPlacement) ? "data-placement=\"" + obj['dataPlacement'].replace(/[\'\"]/g, '&quot;') + "\" " : "";
               result += (obj.dataContainer) ? "data-container=\"" + obj['dataContainer'].replace(/[\'\"]/g, '&quot;') + "\" " : "";
               result += "class=\"help-link\" ";
               result += "><i class=\"icon-question-sign\"></i></a> ";
               break;
            case 'dataTitle':
               result = "data-title=\"" + value + "\" ";
               break;
            case 'columnShow':
               result = "ng-show=\"" + value + "\" ";
               break;
            case 'dataPlacement':
               result = "data-placement=\"" + value + "\" ";
               break;
            case 'dataContainer':
               result = "data-container=\"" + value + "\" ";
               break;
            case 'icon':
               // new method of constructing <i> icon tag. Replces Icon method.
               result = "<i class=\"" + value; 
               result += (obj['iconSize']) ? " icon-" + obj['iconSize'] : "";
               result += "\"></i>";
               break;
            case 'autocomplete':
               result = "autocomplete=\""; 
               result += (value) ? 'true' : 'false';
               result += "\" ";
               break;
            default: 
               result = key + "=\"" + value + "\" ";
        }
        
        return  result; 
        
        }
        })

    .factory('Icon', function() {
    return function(icon) {
        return "<i class=\"" + icon + "\"></i> ";
        }
        })

    .factory('Button', ['Attr', function(Attr) {
    return function(btn, action) {
        // pass in button object, get back html
        var html = '';
        if (btn.awRefresh) {
           html += "<div class=\"refresh-grp pull-right\" ";
           html += (btn.ngShow) ? Attr(btn, 'ngShow') : ""; 
           html += ">\n";
        }
        html += "<button type=\"button\" ";
        html += "class=\"btn";
        if (btn.awRefresh && !btn['class']) {
            html += ' btn-primary btn-xs refresh-btn';
        }
        else if (btn['class']) {
            html += ' ' + btn['class']; 
        }
        else {
            html += " btn-sm";
        }
        html += (btn['awPopOver']) ? " help-link-white" : "";
        html += "\" ";
        html += (btn.ngClick) ? Attr(btn, 'ngClick') : "";
        html += (btn.awRefresh) ? " ng-click=\"refreshCnt = " + $AnsibleConfig.refresh_rate + "; refresh()\" " : "";
        if (btn.id) {
           html += "id=\"" + btn.id + "\" ";
        }
        else {
           if (action) {
              html += "id=\"" + action + "_btn\" "; 
           }
        }
        html += (btn.ngHide) ? Attr(btn,'ngHide') : "";
        html += (btn.awToolTip) ? Attr(btn,'awToolTip') : "";
        html += (btn.awToolTip && btn.dataPlacement == undefined) ? "data-placement=\"top\" " : "";
        html += (btn.awRefresh && !btn.awTooltip) ? "aw-tool-tip=\"Refresh page\" " : "";
        html += (btn.awPopOver) ? "aw-pop-over=\"" + 
            btn.awPopOver.replace(/[\'\"]/g, '&quot;') + "\" " : "";
        html += (btn.dataPlacement) ? Attr(btn, 'dataPlacement') : "";
        html += (btn.dataContainer) ? Attr(btn, 'dataContainer') : "";
        html += (btn.dataTitle) ? Attr(btn, 'dataTitle') : "";
        html += (btn.ngShow) ? Attr(btn, 'ngShow') : "";
        html += (btn.ngHide) ? Attr(btn, 'ngHide') : "";
        html += " >";
        html += (btn['icon']) ? Attr(btn,'icon') : "";
        html += (btn['awRefresh'] && !btn['icon']) ? "<i class=\"icon-refresh\"></i> " : "";
        html += (btn.label) ? " " + btn.label : "";
        html += "</button> ";
        if (btn['awRefresh']) {
           html += '<span class=\"refresh-msg\" aw-refresh>{{ refreshMsg }}</span>\n';
           html += "</div><!-- refresh-grp -->\n";
        }
        return html;
        }
        }])
    
    .factory('NavigationLink', ['Attr', 'Icon', function(Attr, Icon) {
    return function(link) {
        var html = "<a "; 
        html += (link.href) ? Attr(link, 'href') : '';
        html += (link.ngClick) ? Attr(link, 'ngClick') : '';
        html += (link.ngShow) ? Attr(link, 'ngShow') : '';
        html += '>';
        html += (link.icon) ? Icon(link.icon) : '';
        html += (link.label) ? link.label : '';
        html += "</a>\n";
        return html;
        }
        }])

    .factory('DropDown', ['Attr', 'Icon', function(Attr, Icon) {
    return function(params) {
        
        var list = params['list'];
        var fld = params['fld'];
        var options = params['options'];
        var field;
        
        if (params.field) {
           field = params.field; 
        }
        else {
           if (params.type) {
              field = list[params.type][fld];
           }
           else {
              field = list['fields'][fld];
           }
        }

        var name = field['label'].replace(/ /g,'_');

        html = (params.td == undefined || params.td !== false) ? "<td>\n" : "";
        /*
        html += "<div class=\"btn-group\">\n";
        html += "<button type=\"button\" ";
        html += (field.ngDisabled) ? "ng-disabled=\"" + field.ngDisabled + "\" " : "";
        html += "class=\"btn btn-default";
        html += (field['class']) ? " " + field['class'] : " btn-xs"; 
        html += " dropdown-toggle\" data-toggle=\"dropdown\" ";
        html += "id=\"" + name + "_ddown\" ";  
        html += ">";
        html += (field.icon) ? Icon(field.icon) : "";
        html += field.label;
        html += " <span class=\"caret\"></span></button>\n";
        */
        html += "<div class=\"dropdown\">\n";
        html += "<a href=\"\" class=\"toggle btn "; 
        html += (field['class']) ? field['class'] : 'btn-default btn-xs';
        html += "\" ";
        html += (field.ngDisabled) ? "ng-disabled=\"" + field.ngDisabled + "\" " : "";
        html += "data-toggle=\"dropdown\" ";
        html += ">";
        html += (field.icon) ? Icon(field.icon) : "";
        html += field.label;
        html += " <span class=\"caret\"></span></a>\n";
        html += "<ul class=\"dropdown-menu pull-right\" role=\"menu\" aria-labelledby=\"dropdownMenu1\">\n";
        for (var i=0; i < field.options.length; i++) {
            html += "<li role=\"presentation\"><a role=\"menuitem\" tabindex=\"-1\" "; 
            html += "ng-click=\"" + field.options[i].ngClick + "\" ";
            html += (field.options[i].ngShow) ? "ng-show=\"" + field.options[i].ngShow + "\" " : "";
            html += (field.options[i].ngHide) ? "ng-hide=\"" + field.options[i].ngHide + "\" " : "";
            html += "href=\"\">" + field.options[i].label + "</a></li>\n";
        }
        html += "</ul>\n";
        html += "</div>\n";

        html += (params.td == undefined || params.td !== false) ? "</td>\n" : "";
        
        return html;
        
        }  
        }])

    .factory('Badge', [ function() {
    return function(field) {
        
        var html = '';

        if (field.badgeToolTip) {
           html += "<a href=\"\" aw-tool-tip=\"" + field.badgeToolTip + "\"";
           html += (field.badgeTipPlacement) ? " data-placement=\"" + field.badgeTipPlacement + "\"" : "";
           html += (field.badgeShow) ? " ng-show=\"" + field.badgeShow + "\"" : "";
           html += ">";
        } 
        
        html += "<i ";
        html += (field.badgeShow) ? "ng-show=\"" + field.badgeShow + "\" " : "";
        html += " class=\"field-badge " + field.badgeIcon;
        html += (field.badgeClass) ? " " + field.badgeClass : "";
        html += "\"></i>";

        if (field.badgeToolTip) {
           html += "</a>";
        }
        
        html += "\n";

        return html;

        }  
        }])

    .factory('Column', ['Attr', 'Icon', 'DropDown', 'Badge', function(Attr, Icon, DropDown, Badge) {
    return function(params) {
        var list = params['list'];
        var fld = params['fld'];
        var options = params['options'];
        var base = params['base'];

        var field = list['fields'][fld];
        var html = '';
        
        if (field.type !== undefined && field.type == 'DropDown') {
           html = DropDown(params);
        }
        else {
           html += "<td class=\"" + fld + "-column";
           html += (field['class']) ? " " + field['class'] : "";
           html += (field['columnClass']) ? " " + field['columnClass'] : "";
           html +=  "\" ";  
           html += (field.ngClass) ? Attr(field, 'ngClass') : "";
           html += (options.mode == 'lookup' || options.mode == 'select') ? " ng-click=\"toggle_" + list.iterator +"({{ " + list.iterator + ".id }})\"" : "";
           html += (field.columnShow) ? Attr(field, 'columnShow') : "";
           html += ">\n";

           // Add ngShow
           html += (field.ngShow) ? "<span " + Attr(field,'ngShow') + ">" : "";

           // Badge
           if (options.mode !== 'lookup' && field.badgeIcon && field.badgePlacement && field.badgePlacement == 'left') {
              html += Badge(field);
           }
            
           // Add collapse/expand icon  --used on job_events page
           if (list['hasChildren'] && field.hasChildren) {
              html += "<span class=\"level-\{\{ " + list.iterator + ".event_level \}\}\"><a href=\"\" ng-click=\"\{\{ " + list.iterator + ".ngclick \}\}\"> " +
                  "<i class=\"\{\{ " + list.iterator + ".ngicon \}\}\" ng-show=\"'\{\{ " + 
                  list.iterator + ".related.children \}\}' !== ''\" ></i></a> ";
           }

           // Start the Link
           if ((field.key || field.link || field.linkTo || field.ngClick ) && options['mode'] != 'lookup' && options['mode'] != 'select') {
              var cap=false;
              if (field.linkTo) {
                 html += "<a href=\"#" + field.linkTo + "\" ";
                 cap = true;
              }
              else if (field.ngClick) {
                 html += "<a href=\"\"" + Attr(field, 'ngClick') + " ";
                 cap = true;
              }
              else if (field.link || (field.key && (field.link === undefined || field.link))) {
                 html += "<a href=\"#/" + base + "/{{" + list.iterator + ".id }}\" ";
                 cap = true;
              }
              if (field.awToolTip) {
                 html += Attr(field, 'awToolTip');
                 if (field.dataPlacement) {
                    html += Attr(field,'dataPlacement');
                 }
              }
              html += (cap) ? ">" : "";
           }

           // Add icon:
           if (field.ngShowIcon) {
              html += "<i ng-show=\"" + field.ngShowIcon + "\" class=\"" + field.icon + "\"></i> ";
           }
           else {
              if (field.icon) {
                 html += Icon(field.icon) + " ";
              }
           }

           // Add data binds 
           if (field.showValue == undefined || field.showValue == true) {
              if (field.ngBind) {       
                 html += "{{ " + field.ngBind + " }}";
              }
              else {
                 html += "{{" + list.iterator + "." + fld + "}}";   
              }
           }
            
           // Add additional text:
           if (field.text) {
              html += field.text;
           }

           if (list['hasChildren'] && field.hasChildren) {
              html += "</span>";
           }
            
           // close the link
           if ((field.key || field.link || field.linkTo || field.ngClick )
               && options.mode != 'lookup' && options.mode != 'select') {
               html += "</a>";
           }

           // close ngShow
           html += (field.ngShow) ? "</span>" : "";
     
           // Specific to Job Events page -showing event detail/results
           html += (field.appendHTML) ? "<div ng-show=\"" +  field.appendHTML + " !== null\" " + 
               "ng-bind-html-unsafe=\"" + field.appendHTML + "\" " +
               "class=\"level-\{\{ " + list.iterator + ".event_level \}\}-detail\" " +
               "></div>\n" : "";
            
           // Badge
           if (options.mode !== 'lookup' &&  field.badgeIcon && field.badgePlacement && field.badgePlacement !== 'left') {
              html += Badge(field);
           }
        }

        return html += "</td>\n";
    
        }
        }])

    .factory('HelpCollapse', function() {
    return function(params) {
        var hdr = params.hdr; 
        var content = params.content;
        var show = params.show;
        var idx = params.idx;
        var html = '';
        html += "<div class=\"panel-group collapsible-help\" ";
        html += (show) ? "ng-show=\"" + show + "\"" : "";
        html += ">\n";
        html += "<div class=\"panel panel-default\">\n";
        html += "<div class=\"panel-heading\" ng-click=\"accordionToggle('#accordion" + idx + "')\">\n";
        html += "<h4 class=\"panel-title\">\n";
        html += "<i class=\"icon-question-sign help-collapse\"></i> " + hdr;
        html += "<i class=\"icon-minus pull-right collapse-help-icon\" id=\"accordion" + idx + "-icon\"></i>";
        html += "</h4>\n";
        html += "</div>\n";
        html += "<div id=\"accordion" + idx + "\" class=\"panel-collapse collapse in\">\n";
        html += "<div class=\"panel-body\">\n";
        html += content; 
        html += "</div>\n";
        html += "</div>\n";
        html += "</div>\n";
        html += "</div>\n";
        return html;
        }
        })

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
   
        html += "<div class=\"row search-widget\">\n";
        html += "<div class=\""; 
        html += (params.size) ? params.size : "col-lg-4 col-md-6 col-sm-11 col-xs-11";
        html += "\">\n";
        html += (label) ? "<label>" + label +"</label>" : "";
        html += "<div class=\"input-group";
        html += (useMini) ? " input-group-sm" : " input-group-sm";
        html += "\">\n";
        html += "<div class=\"input-group-btn dropdown\">\n";
        
        // Use standard button on mobile
        html += "<button type=\"button\" ";
        html += "id=\"search_field_ddown\" ";
        html += "class=\"btn "; 
        html += "dropdown-toggle\" data-toggle=\"dropdown\"";
        html += ">\n";
        html += "<span ng-bind=\"" + iterator + "SearchFieldLabel\"></span>\n";
        html += "<span class=\"caret\"></span>\n";
        html += "</button>\n";
        
        // Use link and hover activation on desktop
        //html += "<a href=\"\" id=\"search_field_ddown\" class=\"btn btn-default visible-lg\">";
        //html += "<span ng-bind=\"" + iterator + "SearchFieldLabel\"></span>\n";
        //html += "<span class=\"caret\"></span>\n";
        //html += "</a>\n";
        
        html += "<ul class=\"dropdown-menu\" id=\"" + iterator + "SearchDropdown\">\n";
        
        for ( var fld in form.fields) {
          if (form.fields[fld].searchable == undefined || form.fields[fld].searchable == true) {
             html += "<li><a href=\"\" ng-click=\"setSearchField('" + iterator + "','";
             html += fld + "','" + form.fields[fld].label + "')\">" 
                 + form.fields[fld].label + "</a></li>\n";
          }
        }
        html += "</ul>\n";
        html += "</div><!-- input-group-btn -->\n";
        
        html += "<select id=\"search_value_select\" ng-show=\"" + iterator + "SelectShow\" ng-model=\""+ iterator + "SearchSelectValue\" ng-change=\"search('" + iterator + "')\" ";
        html += "ng-options=\"c.name for c in " + iterator + "SearchSelectOpts\" class=\"form-control search-select";
        html += "\"></select>\n";

        html += "<input id=\"search_value_input\" type=\"text\" ng-hide=\"" + iterator + "SelectShow || " + iterator + "InputHide\" class=\"form-control ";
        html += "\" ng-model=\"" + iterator + "SearchValue\" ng-change=\"search('" + iterator + 
                "')\" placeholder=\"Search\" type=\"text\" >\n";
        
        html += "<div class=\"input-group-btn dropdown\">\n";
        html += "<button type=\"button\" ";
        html += "id=\"search_option_ddown\" ";
        html += "ng-hide=\"" + iterator + "SelectShow || " + iterator + "HideSearchType || " + iterator + "InputHide\" class=\"btn ";
        html += "dropdown-toggle\" data-toggle=\"dropdown\">\n";
        html += "<span ng-bind=\"" + iterator + "SearchTypeLabel\"></span>\n";
        html += "<span class=\"caret\"></span>\n";
        html += "</button>\n";
        html += "<ul class=\"dropdown-menu pull-right\">\n";
        html += "<li><a href=\"\" ng-click=\"setSearchType('" + iterator + "','iexact','Exact Match')\">Exact Match</a></li>\n";
        html += "<li><a href=\"\" ng-click=\"setSearchType('" + iterator + "','icontains','Contains')\">Contains</a></li>\n";
        html += "</ul>\n";
        html += "</div><!-- input-group-btn -->\n";
        html += "</div><!-- input-group -->\n";
        html += "</div><!-- col-lg-x -->\n";
        html += "<div class=\"col-lg-1 col-md-1 col-sm-1 col-xs-1\"><i class=\"icon-spinner icon-spin icon-large\" ng-show=\"" + iterator + 
                 "SearchSpin == true\"></i></div>\n";
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
        html += "<button type=\"button\" class=\"previous btn btn-light";
        html += (useMini) ? " btn-xs\" " : "\" ";
        html += "id=\"previous_page_btn\" ";
        html += "ng-click=\"prevSet('" + set + "','" + iterator + "')\" " +
                "ng-disabled=\"" + iterator + "PrevUrl == null || " + iterator + "PrevUrl == undefined\"><i class=\"icon-caret-left\"></i> Prev</button>\n";
        html += "<button type=\"button\" class=\"next btn btn-light";
        html += (useMini) ? " btn-xs\" " : "\" ";
        html += "id=\"next_page_btn\" ";
        html += " ng-click=\"nextSet('" + set + "','" + iterator + "')\"" + 
                "ng-disabled=\"" + iterator + "NextUrl == null || " + iterator + "NextUrl == undefined\">Next <i class=\"icon-caret-right\"></i></button>\n";
        
        if (mode != 'lookup') {
           html += "<label class=\"page-size-label\">Rows per page: </label>\n";
           html += "<select ng-model=\"" + iterator + "PageSize\" ng-change=\"changePageSize('" + 
                    set + "'," + "'" + iterator + "')\" ";
           html += "id=\"page_size_select\" ";
           html += "class=\"page-size\">\n";
           html += "<option value=\"10\" selected>10</option>\n";
           html += "<option value=\"20\" selected>20</option>\n";
           html += "<option value=\"40\">40</option>\n";
           html += "<option value=\"60\">60</option>\n";
           html += "<option value=\"80\">80</option>\n";    
           html += "</select>\n";
        }

        html += "<div class=\"page-number-small pull-right\" ng-show=\"" + iterator + "PageCount > 0\" ";
        html += ">Page: {{ " + iterator + "Page + 1 }} of {{ " + iterator + "PageCount }}</div>\n";
        html += "</form>\n";
        html += "</div>\n";

        return html;

        }
        });