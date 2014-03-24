/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * GeneratorHelpers
 *
 * Functions shared between FormGenerator and ListGenerator
 *
 */

'use strict';

angular.module('GeneratorHelpers', [])

.factory('Attr', function () {
    return function (obj, key, fld) {
        var i, s, result,
            value = (typeof obj[key] === "string") ? obj[key].replace(/[\'\"]/g, '&quot;') : obj[key];

        if (/^ng/.test(key)) {
            result = 'ng-' + key.replace(/^ng/, '').toLowerCase() + "=\"" + value + "\" ";
        } else if (/^data|^aw/.test(key) && key !== 'awPopOver') {
            s = '';
            for (i = 0; i < key.length; i++) {
                if (/[A-Z]/.test(key.charAt(i))) {
                    s += '-' + key.charAt(i).toLowerCase();
                } else {
                    s += key.charAt(i);
                }
            }
            result = s + "=\"" + value + "\" ";
        } else {
            switch (key) {
            case 'trueValue':
                result = "ng-true-value=\"" + value + "\" ";
                break;
            case 'falseValue':
                result = "ng-false-value=\"" + value + "\" ";
                break;
            case 'awPopOver':
                // construct the entire help link
                result = "<a id=\"awp-" + fld + "\" href=\"\" aw-pop-over=\'" + value + "<div class=\"popover-footer\"><span class=\"key\">esc</span> or click to close</div>\' ";
                result += (obj.dataPlacement) ? "data-placement=\"" + obj.dataPlacement + "\" " : "";
                result += (obj.dataContainer) ? "data-container=\"" + obj.dataContainer + "\" " : "";
                result += (obj.dataTitle) ? "data-title=\"" + obj.dataTitle + "\" " : "";
                result += (obj.dataTrigger) ? "data-trigger=\"" + obj.dataTrigger + "\" " : "";
                result += "class=\"help-link\" ";
                result += "><i class=\"fa fa-question-circle\"></i></a> ";
                break;
            case 'columnShow':
                result = "ng-show=\"" + value + "\" ";
                break;
            case 'icon':
                // new method of constructing <i> icon tag. Replces Icon method.
                result = "<i class=\"fa fa-" + value;
                result += (obj.iconSize) ? " " + obj.iconSize : "";
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
        }

        return result;

    };
})

.factory('Icon', function () {
    return function (icon) {
        return "<i class=\"fa " + icon + "\"></i> ";
    };
})

.factory('SelectIcon', ['Icon',
    function (Icon) {
        return function (params) {
            // Common point for matching any type of action to the appropriate 
            // icon. The intention is to maintain consistent meaning and presentation
            // for every icon used in the application.
            var icon,
                action = params.action,
                size = params.size;
            switch (action) {
            case 'help':
                icon = "fa-question-circle";
                break;
            case 'add':
            case 'create':
                icon = "fa-plus";
                break;
            case 'edit':
                icon = "fa-pencil";
                break;
            case 'delete':
                icon = "fa-trash-o";
                break;
            case 'group_update':
                icon = 'fa-exchange';
                break;
            case 'scm_update':
                icon = 'fa-cloud-download';
                break;
            case 'cancel':
                icon = 'fa-minus-circle';
                break;
            case 'run':
            case 'rerun':
            case 'submit':
                icon = 'fa-rocket';
                break;
            case 'stream':
                icon = 'fa-clock-o';
                break;
            case 'refresh':
                icon = 'fa-refresh';
                break;
            case 'close':
                icon = 'fa-arrow-left';
                break;
            case 'save':
                icon = 'fa-check-square-o';
                break;
            case 'properties':
                icon = "fa-wrench";
                break;
            case 'reset':
                icon = "fa-undo";
                break;
            case 'view':
                icon = "fa-search-plus";
                break;
            case 'sync_status':
                icon = "fa-cloud";
                break;
            case 'schedule':
                icon = "fa-calendar";
                break;
            }
            icon += (size) ? " " + size : "";
            return Icon(icon);
        };
    }
])


.factory('Button', ['Attr', 'SelectIcon',
    function (Attr, SelectIcon) {
        return function (params) {

            // pass in button object, get back html

            var btn = params.btn,
                action = params.action, // label used to select the icon
                toolbar = params.toolbar,
                html = '';

            if (toolbar) {
                //if this is a toolbar button, set some defaults
                btn.class = 'btn-xs btn-primary';
                btn.iconSize = 'fa-lg';
                delete btn.label;
            }

            html += "<button type=\"button\" ";
            html += "class=\"btn";

            if (btn['class']) {
                html += ' ' + btn['class'];
            } else {
                html += " btn-sm";
            }

            html += (btn.awPopOver) ? " help-link-white" : "";
            html += "\" ";
            html += (btn.ngClick) ? Attr(btn, 'ngClick') : "";

            if (btn.id) {
                html += "id=\"" + btn.id + "\" ";
            } else {
                if (action) {
                    html += "id=\"" + action + "_btn\" ";
                }
            }

            html += (btn.ngHide) ? Attr(btn, 'ngHide') : "";
            html += (btn.awToolTip) ? Attr(btn, 'awToolTip') : "";
            html += (btn.awToolTip && btn.dataPlacement === undefined) ? "data-placement=\"top\" " : "";
            html += (btn.awPopOver) ? "aw-pop-over=\"" +
                btn.awPopOver.replace(/[\'\"]/g, '&quot;') + "\" " : "";
            html += (btn.dataPlacement) ? Attr(btn, 'dataPlacement') : "";
            html += (btn.dataContainer) ? Attr(btn, 'dataContainer') : "";
            html += (btn.dataTitle) ? Attr(btn, 'dataTitle') : "";
            html += (btn.ngShow) ? Attr(btn, 'ngShow') : "";
            html += (btn.ngHide) ? Attr(btn, 'ngHide') : "";
            html += (btn.ngDisabled) ? Attr(btn, 'ngHide') : "";
            html += (btn.ngClass) ? Attr(btn, 'ngClass') : "";
            html += (btn.awTipPlacement) ? Attr(btn, 'awTipPlacement') : "";
            html += " >";
            html += (btn.img) ? "<img src=\"" + $basePath + "img/" + btn.img + "\" style=\"width: 12px; height: 12px;\" >" : "";

            html += SelectIcon({
                action: action,
                size: btn.iconSize
            });

            html += (btn.label) ? " " + btn.label : "";
            html += "</button> ";

            return html;
        };
    }
])


.factory('NavigationLink', ['Attr', 'Icon',
    function (Attr, Icon) {
        return function (link) {
            var html = "<a ";
            html += (link.href) ? Attr(link, 'href') : '';
            html += (link.ngClick) ? Attr(link, 'ngClick') : '';
            html += (link.ngShow) ? Attr(link, 'ngShow') : '';
            html += '>';
            html += (link.icon) ? Icon(link.icon) : '';
            html += (link.label) ? link.label : '';
            html += "</a>\n";
            return html;
        };
    }
])


.factory('DropDown', ['Attr', 'Icon',
    function (Attr, Icon) {
        return function (params) {

            var list = params.list,
                fld = params.fld,
                i, html, field, name;

            if (params.field) {
                field = params.field;
            } else {
                if (params.type) {
                    field = list[params.type][fld];
                } else {
                    field = list.fields[fld];
                }
            }

            name = field.label.replace(/ /g, '_');

            if (params.td === undefined || params.td !== false) {
                html = "<td class=\"" + fld + "-column\">\n";
            } else {
                html = '';
            }

            html += "<div class=\"dropdown\">\n";
            html += "<a href=\"\" class=\"toggle";
            html += "\" ";
            html += (field.ngDisabled) ? "ng-disabled=\"" + field.ngDisabled + "\" " : "";
            html += "data-toggle=\"dropdown\" ";
            html += ">";
            html += (field.icon) ? Icon(field.icon) : "";
            html += field.label;
            html += " <span class=\"caret\"></span></a>\n";
            html += "<ul class=\"dropdown-menu pull-right\" role=\"menu\" aria-labelledby=\"dropdownMenu1\">\n";
            for (i = 0; i < field.options.length; i++) {
                html += "<li role=\"presentation\"><a role=\"menuitem\" tabindex=\"-1\" ";
                html += (field.options[i].ngClick) ? "ng-click=\"" + field.options[i].ngClick + "\" " : "";
                html += (field.options[i].ngHref) ? "ng-href=\"" + field.options[i].ngHref + "\" " : "";
                html += (field.options[i].ngShow) ? "ng-show=\"" + field.options[i].ngShow + "\" " : "";
                html += (field.options[i].ngHide) ? "ng-hide=\"" + field.options[i].ngHide + "\" " : "";
                html += "href=\"\">" + field.options[i].label + "</a></li>\n";
            }

            html += "</ul>\n";
            html += "</div>\n";
            html += (params.td === undefined || params.td !== false) ? "</td>\n" : "";

            return html;

        };
    }
])

.factory('BadgeCount', [
    function () {
        return function (params) {

            // Adds a badge count with optional tooltip

            var list = params.list,
                fld = params.fld,
                field = list.fields[fld],
                html;

            html = "<td class=\"" + fld + "-column";
            html += (field.columnClass) ? " " + field.columnClass : "";
            html += "\">\n";
            html += "<a ng-href=\"" + field.ngHref + "\" aw-tool-tip=\"" + field.awToolTip + "\"";
            html += (field.dataPlacement) ? " data-placement=\"" + field.dataPlacement + "\"" : "";
            html += ">";
            html += "<span class=\"badge";
            html += (field['class']) ? " " + field['class'] : "";
            html += "\">";
            html += "{{ " + list.iterator + '.' + fld + " }}";
            html += "</span>";
            html += (field.badgeLabel) ? " " + field.badgeLabel : "";
            html += "</a>\n";
            html += "</td>\n";
            return html;
        };
    }
])

.factory('Badge', [
    function () {
        return function (field) {

            // Adds an icon(s) with optional tooltip

            var i, html = '';

            if (field.badges) {
                for (i = 0; i < field.badges.length; i++) {
                    if (field.badges[i].toolTip) {
                        html += "<a href=\"\" aw-tool-tip=\"" + field.badges[i].toolTip + "\"";
                        html += (field.badges[i].toolTipPlacement) ? " data-placement=\"" + field.badges[i].toolTipPlacement + "\"" : "";
                        html += (field.badges[i].badgeShow) ? " ng-show=\"" + field.badges[i].badgeShow + "\"" : "";
                        html += ">";
                    }
                    html += "<i ";
                    html += (field.badges[i].badgeShow) ? "ng-show=\"" + field.badges[i].badgeShow + "\" " : "";
                    html += " class=\"field-badge " + field.badges[i].icon;
                    html += (field.badges[i].badgeClass) ? " " + field.badges[i].badgeClass : "";
                    html += "\"></i>";
                    if (field.badges[i].toolTip) {
                        html += "</a>";
                    }
                    html += "\n";
                }
            } else {
                if (field.badgeToolTip) {
                    html += "<a ";
                    html += (field.badgeNgHref) ? "ng-href=\"" + field.badgeNgHref + "\" " : "href=\"\"";
                    html += (field.ngClick) ? "ng-click=\"" + field.ngClick + "\" " : "";
                    html += " aw-tool-tip=\"" + field.badgeToolTip + "\"";
                    html += (field.badgeTipPlacement) ? " data-placement=\"" + field.badgeTipPlacement + "\"" : "";
                    html += (field.badgeTipWatch) ? " data-tip-watch=\"" + field.badgeTipWatch + "\"" : "";
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
            }
            return html;
        };
    }
])

.factory('Breadcrumbs', ['Attr',
    function (Attr) {
        return function (params) {

            // Generate breadcrumbs using the list-generator.js method.

            var list = params.list,
                mode = params.mode,
                html = '', itm, navigation;

            html += "<div class=\"nav-path\">\n";
            html += "<ul class=\"breadcrumb\" id=\"breadcrumb-list\">\n";
            html += "<li ng-repeat=\"crumb in breadcrumbs\"><a href=\"{{ '#' + crumb.path }}\">{{ crumb.title }}</a></li>\n";

            if (list.navigationLinks) {
                navigation = list.navigationLinks;
                if (navigation.ngHide) {
                    html += "<li class=\"active\" ng-show=\"" + navigation.ngHide + "\">";
                    html += list.editTitle;
                    html += "</li>\n";
                    html += "<li class=\"active\" ng-hide=\"" + navigation.ngHide + "\"> </li>\n";
                } else {
                    html += "<li class=\"active\"> </li>\n";
                    html += "</ul>\n";
                }
                html += "<div class=\"dropdown\" ";
                html += (navigation.ngHide) ? Attr(navigation, 'ngHide') : '';
                html += ">\n";
                for (itm in navigation) {
                    if (typeof navigation[itm] === 'object' && navigation[itm].active) {
                        html += "<a href=\"\" class=\"toggle\" ";
                        html += "data-toggle=\"dropdown\" ";
                        html += ">" + navigation[itm].label + " <i class=\"fa fa-chevron-circle-down crumb-icon\"></i></a>";
                        break;
                    }
                }
                html += "<ul class=\"dropdown-menu\" role=\"menu\">\n";
                for (itm in navigation) {
                    if (typeof navigation[itm] === 'object') {
                        html += "<li role=\"presentation\"><a role=\"menuitem\" tabindex=\"-1\" href=\"" +
                            navigation[itm].href + "\" ";
                        // html += (navigation[itm].active) ? "class=\"active\" " : "";
                        html += ">";
                        html += "<i class=\"fa fa-check\" style=\"visibility: ";
                        html += (navigation[itm].active) ? "visible" : "hidden";
                        html += "\"></i> ";
                        html += navigation[itm].label;
                        html += "</a></li>\n";
                    }
                }
                html += "</ul>\n";
                html += "</div><!-- dropdown -->\n";
                html += "</div><!-- nav-path -->\n";
            } else {
                html += "<li class=\"active\">";
                if (mode === 'select') {
                    html += list.selectTitle;
                } else {
                    html += list.editTitle;
                }
                html += "</li>\n</ul>\n</div>\n";
            }

            return html;

        };
    }
])

.factory('Column', ['Attr', 'Icon', 'DropDown', 'Badge', 'BadgeCount',
    function (Attr, Icon, DropDown, Badge, BadgeCount) {
        return function (params) {
            var list = params.list,
                fld = params.fld,
                options = params.options,
                base = params.base,
                field = list.fields[fld],
                html = '', cap;

            if (field.type !== undefined && field.type === 'DropDown') {
                html = DropDown(params);
            } else if (field.type === 'badgeCount') {
                html = BadgeCount(params);
            } else {
                html += "<td class=\"" + fld + "-column";
                html += (field['class']) ? " " + field['class'] : "";
                html += (field.columnClass) ? " " + field.columnClass : "";
                html += "\" ";
                html += (field.ngClass) ? Attr(field, 'ngClass') : "";
                html += (options.mode === 'lookup' || options.mode === 'select') ? " ng-click=\"toggle_" + list.iterator +
                    "(" + list.iterator + ".id)\"" : "";
                html += (field.columnShow) ? Attr(field, 'columnShow') : "";
                html += (field.ngBindHtml) ? "ng-bind-html=\"" + field.ngBindHtml + "\" " : "";
                html += (field.columnClick) ? "ng-click=\"" + field.columnClick + "\" " : "";
                html += ">\n";

                // Add ngShow
                html += (field.ngShow) ? "<span " + Attr(field, 'ngShow') + ">" : "";

                // Badge
                if (options.mode !== 'lookup' && (field.badges || (field.badgeIcon && field.badgePlacement && field.badgePlacement === 'left'))) {
                    html += Badge(field);
                }

                // Add collapse/expand icon  --used on job_events page
                if (list.hasChildren && field.hasChildren) {
                    html += "<div class=\"level level-{{ " + list.iterator + ".event_level }}\"><a href=\"\" ng-click=\"toggle(" +
                        list.iterator + ".id)\"> " +
                        "<i class=\"{{ " + list.iterator + ".ngicon }}\"></i></a></div>";
                    //ng-show=\"'\{\{ " + list.iterator + ".related.children \}\}' !== ''\"
                }

                if (list.name === 'groups') {
                    html += "<div class=\"group-name\">";
                }
                if (list.name === 'hosts') {
                    html += "<div class=\"host-name\">";
                }

                // Start the Link
                if ((field.key || field.link || field.linkTo || field.ngClick || field.ngHref) &&
                    options.mode !== 'lookup' && options.mode !== 'select' && !field.noLink && !field.ngBindHtml) {
                    cap = false;
                    if (field.linkTo) {
                        html += "<a href=\"" + field.linkTo + "\" ";
                        cap = true;
                    } else if (field.ngClick) {
                        html += "<a href=\"\"" + Attr(field, 'ngClick') + " ";
                        cap = true;
                    } else if (field.ngHref) {
                        html += "<a ng-href=\"" + field.ngHref + "\" ";
                        cap = true;
                    } else if (field.link || (field.key && (field.link === undefined || field.link))) {
                        html += "<a href=\"#/" + base + "/{{" + list.iterator + ".id }}\" ";
                        cap = true;
                    }
                    if (field.awDroppable) {
                        html += Attr(field, 'awDroppable');
                        html += (field.dataAccept) ? Attr(field, 'dataAccept') : '';
                    }
                    if (field.awDraggable) {
                        html += Attr(field, 'awDraggable');
                        html += (field.dataContainment) ? Attr(field, 'dataContainment') : '';
                        html += (field.dataTreeId) ? Attr(field, 'dataTreeId') : '';
                        html += (field.dataGroupId) ? Attr(field, 'dataGroupId') : '';
                        html += (field.dataHostId) ? Attr(field, 'dataHostId') : '';
                        html += (field.dataType) ? Attr(field, 'dataType') : '';
                    }
                    if (field.awToolTip) {
                        html += Attr(field, 'awToolTip');
                        html += (field.dataPlacement) ? Attr(field, 'dataPlacement') : "";
                        html += (field.dataTipWatch) ? Attr(field, 'dataTipWatch') : "";
                    }
                    html += (cap) ? ">" : "";
                }

                // Add icon:
                if (field.ngShowIcon) {
                    html += "<i ng-show=\"" + field.ngShowIcon + "\" class=\"" + field.icon + "\"></i> ";
                } else {
                    if (field.icon) {
                        html += Icon(field.icon) + " ";
                    }
                }

                // Add data binds 
                if (!field.ngBindHtml && (field.showValue === undefined || field.showValue === true)) {
                    if (field.ngBind) {
                        html += "{{ " + field.ngBind;
                    } else {
                        html += "{{" + list.iterator + "." + fld;
                    }
                    if (field.filter) {
                        html += " | " + field.filter + " }}";
                    }
                    else {
                        html += " }}";
                    }
                }

                // Add additional text:
                if (field.text) {
                    html += field.text;
                }

                //if (list['hasChildren'] && field.hasChildren) {
                //   html += "</span>";
                //}

                // close the link
                if ((field.key || field.link || field.linkTo || field.ngClick || field.ngHref) &&
                    options.mode !== 'lookup' && options.mode !== 'select' && !field.noLink && !field.ngBindHtml) {
                    html += "</a>";
                }

                if (list.name === 'hosts' || list.name === 'groups') {
                    html += "</div>";
                }

                // close ngShow
                html += (field.ngShow) ? "</span>" : "";

                // Specific to Job Events page -showing event detail/results
                html += (field.appendHTML) ? "<div ng-show=\"" + field.appendHTML + " !== null\" " +
                    "ng-bind-html-unsafe=\"" + field.appendHTML + "\" " +
                    "class=\"level-{{ " + list.iterator + ".event_level }}-detail\" " +
                    "></div>\n" : "";

                // Badge
                if (options.mode !== 'lookup' && field.badgeIcon && field.badgePlacement && field.badgePlacement !== 'left') {
                    html += Badge(field);
                }
            }
            return html += "</td>\n";
        };
    }
])

.factory('HelpCollapse', function () {
    return function (params) {
        
        var hdr = params.hdr,
            content = params.content,
            show = params.show,
            idx = params.idx,
            bind = params.bind,
            html = '';
        
        html += "<div class=\"panel-group collapsible-help\" ";
        html += (show) ? "ng-show=\"" + show + "\"" : "";
        html += ">\n";
        html += "<div class=\"panel panel-default\">\n";
        html += "<div class=\"panel-heading\" ng-click=\"accordionToggle('#accordion" + idx + "')\">\n";
        html += "<h4 class=\"panel-title\">\n";
        //html += "<i class=\"fa fa-question-circle help-collapse\"></i> " + hdr;
        html += hdr;
        html += "<i class=\"fa fa-minus pull-right collapse-help-icon\" id=\"accordion" + idx + "-icon\"></i>";
        html += "</h4>\n";
        html += "</div>\n";
        html += "<div id=\"accordion" + idx + "\" class=\"panel-collapse collapse in\">\n";
        html += "<div class=\"panel-body\" ";
        html += (bind) ? "ng-bind-html-unsafe=\"" + bind + "\" " : "";
        html += ">\n";
        html += (!bind) ? content : "";
        html += "</div>\n";
        html += "</div>\n";
        html += "</div>\n";
        html += "</div>\n";
        return html;
    };
})

.factory('SearchWidget', function () {
    return function (params) {
        //
        // Generate search widget
        //
        var iterator = params.iterator,
            form = params.template,
            size = params.size,
            includeSize = (params.includeSize === undefined) ? true : params.includeSize,
            fld,
            i, html = '',
            modifier,
            searchWidgets = (params.searchWidgets) ? params.searchWidgets : 1;

        for (i = 1; i <= searchWidgets; i++) {
            modifier = (i === 1) ? '' : i;
    
            if (includeSize) {
                html += "<div class=\"";
                html += (size) ? size : "col-lg-4 col-md-6 col-sm-12 col-xs-12";
                html += "\" id=\"search-widget-container" + modifier + "\">\n";
            }

            html += "<div class=\"input-group input-group-sm";
            html += "\">\n";
            html += "<div class=\"input-group-btn dropdown\">\n";
            html += "<button type=\"button\" ";
            html += "id=\"search_field_ddown\" ";
            html += "class=\"btn btn-default ";
            html += "dropdown-toggle\" data-toggle=\"dropdown\"";
            html += ">\n";
            html += "<span ng-bind=\"" + iterator + "SearchFieldLabel" + modifier + "\"></span>\n";
            html += "<span class=\"caret\"></span>\n";
            html += "</button>\n";
            html += "<ul class=\"dropdown-menu\" id=\"" + iterator + "SearchDropdown" + modifier + "\">\n";
            for (fld in form.fields) {
                if ((form.fields[fld].searchable === undefined || form.fields[fld].searchable === true) &&
                    (((form.fields[fld].searchWidget === undefined || form.fields[fld].searchWidget === 1) && i === 1) ||
                    (form.fields[fld].searchWidget === i))) {
                    html += "<li><a href=\"\" ng-click=\"setSearchField('" + iterator + "','";
                    html += fld + "','";
                    if (form.fields[fld].searchLabel) {
                        html += form.fields[fld].searchLabel + "', " + i + ")\">" +
                            form.fields[fld].searchLabel + "</a></li>\n";
                    } else {
                        html += form.fields[fld].label.replace(/<br \/>/g, ' ') + "', " + i + ")\">" +
                            form.fields[fld].label.replace(/<br \/>/g, ' ') + "</a></li>\n";
                    }
                }
            }
            html += "</ul>\n";
            html += "</div><!-- input-group-btn -->\n";

            html += "<select id=\"search_value_select\" ng-show=\"" + iterator + "SelectShow" + modifier + "\" " +
                "ng-model=\"" + iterator + "SearchSelectValue" + modifier + "\" ng-change=\"search('" + iterator + "')\" ";
            html += "ng-options=\"c.name for c in " + iterator + "SearchSelectOpts" + modifier + "\" class=\"form-control search-select";
            html += "\"></select>\n";


            html += "<input id=\"search_value_input\" type=\"text\" ng-hide=\"" + iterator + "SelectShow" + modifier + " || " +
                iterator + "InputHide" + modifier + "\" " +
                "class=\"form-control\" ng-model=\"" + iterator + "SearchValue" + modifier + "\" " +
                "aw-placeholder=\"" + iterator + "SearchPlaceholder" + modifier + "\" type=\"text\" ng-disabled=\"" + iterator +
                "InputDisable" + modifier + " || " + iterator + "HoldInput" + modifier + "\" ng-keypress=\"startSearch($event,'" +
                iterator + "')\">\n";

            // Reset button for drop-down
            html += "<div class=\"input-group-btn\" ng-show=\"" + iterator + "SelectShow" + modifier + "\" >\n";
            html += "<button type=\"button\" class=\"btn btn-default btn-small\" ng-click=\"resetSearch('" + iterator + "')\" " +
                "aw-tool-tip=\"Clear the search\" data-placement=\"top\"><i class=\"fa fa-times\"></i></button>\n";
            html += "</div><!-- input-group-btn -->\n";

            html += "</div><!-- input-group -->\n";

            html += "<a class=\"search-reset-start\" ng-click=\"resetSearch('" + iterator + "')\"" +
                "ng-hide=\"" + iterator + "SelectShow" + modifier + " || " + iterator + "InputHide" + modifier + " || " +
                iterator + "ShowStartBtn" + modifier + " || " +
                iterator + "HoldInput" + modifier + " || " +
                iterator + "HideAllStartBtn" + modifier + "\"" +
                "><i class=\"fa fa-times\"></i></a>\n";

            html += "<a class=\"search-reset-start\" ng-click=\"search('" + iterator + "')\"" +
                "ng-hide=\"" + iterator + "SelectShow" + modifier + " || " + iterator + "InputHide" + modifier + " || " +
                "!" + iterator + "ShowStartBtn" + modifier + " || " +
                iterator + "HoldInput" + modifier + " || " +
                iterator + "HideAllStartBtn" + modifier + "\"" +
                "><i class=\"fa fa-search\"></i></a>\n";
            
            if (includeSize) {
                html += "</div>\n";
            }
        }

        return html;

    };
})

.factory('PaginateWidget', [
    function () {
        return function (params) {
            var iterator = params.iterator,
                set = params.set,
                html = '';
            html += "<!-- Paginate Widget -->\n";
            html += "<div class=\"row page-row\">\n";
            html += "<div class=\"col-lg-8 col-md-8\">\n";
            html += "<ul class=\"pagination\" ng-hide=\"" + iterator + "Loading || " + iterator + "_num_pages <= 1\">\n";
            html += "<li ng-hide=\"" + iterator + "_page -5 <= 1 \"><a href ng-click=\"getPage(1,'" + set + "','" + iterator + "')\">" +
                "<i class=\"fa fa-angle-double-left\"></i></a></li>\n";
            html += "<li ng-hide=\"" + iterator + "_page -1 <= 0\"><a href " +
                "ng-click=\"getPage(" + iterator + "_page - 1,'" + set + "','" + iterator + "')\">" +
                "<i class=\"fa fa-angle-left\"></i></a></li>\n";
            html += "<li ng-repeat=\"page in " + iterator + "_page_range\" ng-class=\"pageIsActive(page,'" + iterator + "')\">" +
                "<a href ng-click=\"getPage(page,'" + set + "','" + iterator + "')\">{{ page }}</a></li>\n";
            html += "<li ng-hide=\"" + iterator + "_page + 1 > " + iterator + "_num_pages\"><a href ng-click=\"" +
                "getPage(" + iterator + "_page + 1,'" + set + "','" + iterator + "')\"><i class=\"fa fa-angle-right\"></i></a></li>\n";
            html += "<li ng-hide=\"" + iterator + "_page +4 >= " + iterator + "_num_pages\"><a href ng-click=\"" +
                "getPage(" + iterator + "_num_pages,'" + set + "','" + iterator + "')\"><i class=\"fa fa-angle-double-right\"></i></a></li>\n";
            html += "</ul>\n";
            html += "</div>\n";
            html += "<div class=\"col-lg-4 col-md-4\" ng-hide=\"" + iterator + "_mode == 'lookup'\">\n";
            html += "<div class=\"page-label\">\n";
            html += "Page {{ " + iterator + "_page }} of {{ " + iterator + "_num_pages }} for {{ " + iterator + "_total_rows | number:0 }} " +
                set.replace(/\_/g,' ') + '.';
            html += "</div>\n";
            html += "</div>\n";
            html += "</div>\n";

            return html;
        };
    }
]);