/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 */
  /**
 *  @ngdoc function
 *  @name shared.function:generator-helpers
 *  @description
 * GeneratorHelpers
 *
 * Functions shared between FormGenerator and ListGenerator
 *
 */
 import systemStatus from 'tower/smart-status/main';


export default
angular.module('GeneratorHelpers', [systemStatus.name])

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
                result = "<a id=\"awp-" + fld + "\" href=\"\" aw-pop-over=\'" + value + "\' ";
                result += (obj.dataPlacement) ? "data-placement=\"" + obj.dataPlacement + "\" " : "";
                result += (obj.dataContainer) ? "data-container=\"" + obj.dataContainer + "\" " : "";
                result += (obj.dataTitle) ? "data-title=\"" + obj.dataTitle + "\" " : "";
                result += (obj.dataTrigger) ? "data-trigger=\"" + obj.dataTrigger + "\" " : "";
                result += (obj.awPopOverWatch) ? "aw-pop-over-watch=\"" + obj.awPopOverWatch + "\" " : "";
                result += "class=\"help-link\" ";
                result += "><i class=\"fa fa-question-circle\"></i></a> ";
                break;
            case 'columnShow':
                result = "ng-show=\"" + value + "\" ";
                break;
            case 'iconName':
                result = "icon-name=\"" + value + "\" ";
                break;
            case 'iconSize':
                result = "icon-size=\"" + value + "\" ";
                break;
            case 'icon':
                // new method of constructing <i> icon tag. Replaces Icon method.
                result = "<i class=\"fa fa-" + value;
                result += (obj.iconSize) ? " " + obj.iconSize : "";
                result += "\"></i>";
                break;
            case 'autocomplete':
                result = "autocomplete=\"";
                result += (value) ? 'true' : 'false';
                result += "\" ";
                break;
            case 'columnClass':
                result = 'class="';
                result += value;
                result += '"';
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
            case 'launch':
                icon = 'fa-rocket';
                break;
            case 'stream':
                icon = 'fa-clock-o';
                break;
            case 'socket':
                icon = 'fa-power-off';
                break;
            case 'refresh':
                icon = 'fa-refresh';
                break;
            case 'close':
                icon = 'fa-arrow-left';
                break;
            case 'save':
            case 'form_submit':
                icon = 'fa-check-square-o';
                break;
            case 'properties':
                icon = "fa-pencil";
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
            case 'stdout':
                icon = "fa-external-link";
                break;
            case 'question_cancel':
                icon = 'fa-times';
                break;
            case 'job_details':
                icon = 'fa-list-ul';
                break;
            case 'copy':
                icon = "fa-copy";
                break;
            }
            icon += (size) ? " " + size : "";
            return Icon(icon);
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
            html += (field.ngShow) ? "ng-show=\"" + field.ngShow + "\" " : "";
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
            html += (field.columnNgClass) ? "\" ng-class=\"" + field.columnNgClass : "";
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
                html += " class=\"fa " + field.badgeIcon;
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

.factory('Breadcrumbs', ['$rootScope', 'Attr',
    function ($rootScope, Attr) {
        return function (params) {

            // Generate breadcrumbs using the list-generator.js method.

            var list = params.list,
                mode = params.mode,
                html = '', itm, navigation;

            html += "<ul class=\"ansible-breadcrumb\" id=\"breadcrumb-list\">\n";
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
            } else {
                html += "<li class=\"active\"><a href=\"\">";
                if (mode === 'select') {
                    html += list.selectTitle;
                } else {
                    html += list.editTitle;
                }
                html += "</a></li>\n</ul>\n";
            }

            return html;

        };
    }
])

// List field with multiple icons
.factory('BuildLink', ['Attr', 'Icon', function(Attr, Icon){
    return function(params) {
        var html = '',
            field = params.field,
            list = params.list,
            base = params.base,
            fld = params.fld;

        if (field.linkTo) {
            html += "<a href=\"" + field.linkTo + "\" ";
        } else if (field.ngClick) {
            html += "<a href=\"\" " + Attr(field, 'ngClick') + " ";
        } else if (field.ngHref) {
            html += "<a ng-href=\"" + field.ngHref + "\" ";
        } else if (field.link || (field.key && (field.link === undefined || field.link))) {
            html += "<a href=\"#/" + base + "/{{" + list.iterator + ".id }}\" ";
        } else {
            html += "<a href=\"\">";
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
            html += (field.dataPlacement && !field.awPopOver) ? Attr(field, 'dataPlacement') : "";
            html += (field.dataTipWatch) ? Attr(field, 'dataTipWatch') : "";
            html += (field.awTipPlacement) ? Attr(field, 'awTipPlacement') : "";
        }
        if (field.awToolTipEllipses) {
            html += Attr(field, 'awToolTipEllipses');
            html += (field.dataPlacement && !field.awPopOver) ? Attr(field, 'dataPlacement') : "";
            html += (field.dataTipWatch) ? Attr(field, 'dataTipWatch') : "";
            html += (field.awTipPlacement) ? Attr(field, 'awTipPlacement') : "";
        }
        if (field.awPopOver) {
            html += "aw-pop-over=\"" + field.awPopOver + "\" ";
            html += (field.dataPlacement) ? "data-placement=\"" + field.dataPlacement + "\" " : "";
            html += (field.dataTitle) ? "data-title=\"" + field.dataTitle + "\" " : "";
        }
        html += (field.ngClass) ? Attr(field, 'ngClass') : '';
        html += (field.ngEllipsis) ? "data-ng-bind=\"" + list.iterator + "." + fld + "\" data-ellipsis " : "";
        html += ">";

        // Add icon:
        if (field.ngShowIcon) {
            html += "<i ng-show=\"" + field.ngShowIcon + "\" class=\"" + field.icon + "\"></i> ";
        } else if (field.icon) {
            html += Icon(field.icon) + " ";
        }

        // Add data binds
        if (!field.ngBindHtml && !field.iconOnly && !field.ngEllipsis && (field.showValue === undefined || field.showValue === true)) {
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
        html += "</a>";
        return html;
    };
}])

.factory('Template', ['Attr', function(Attr) {
    return function(field) {
        var ngClass = (field.ngClass) ? Attr(field, 'ngClass') : null;
        var classList = (field.columnClass) ? Attr(field, 'columnClass') : null;
        var ngInclude = (field.ngInclude) ? Attr(field, 'ngInclude') : null;
        var attrs = _.compact([ngClass, classList, ngInclude]);

        return '<td ' + attrs.join(' ') + '></td>';
    };
}])

.factory('Column', ['Attr', 'Icon', 'DropDown', 'Badge', 'BadgeCount', 'BuildLink', 'Template',
    function (Attr, Icon, DropDown, Badge, BadgeCount, BuildLink, Template) {
        return function (params) {
            var list = params.list,
                fld = params.fld,
                options = params.options,
                base = params.base,
                field = list.fields[fld],
                html = '';

            if (field.type !== undefined && field.type === 'DropDown') {
                html = DropDown(params);
            } else if (field.type === 'badgeCount') {
                html = BadgeCount(params);
            } else if (field.type === 'badgeOnly') {
                html = Badge(field);
            } else if (field.type === 'template') {
                html = Template(field);
            } else {
                html += "<td class=\"" + fld + "-column";
                html += (field['class']) ? " " + field['class'] : "";
                if (options.mode === 'lookup' && field.modalColumnClass) {
                    html += " " + field.modalColumnClass;
                }
                else if (field.columnClass) {
                    html += " " + field.columnClass;
                }
                html += "\" ";
                html += field.columnNgClass ? " ng-class=\"" + field.columnNgClass + "\"": "";
                html += (options.mode === 'lookup' || options.mode === 'select') ? " ng-click=\"toggle_" + list.iterator +
                    "(" + list.iterator + ".id)\"" : "";
                html += (field.columnShow) ? Attr(field, 'columnShow') : "";
                html += (field.ngBindHtml) ? "ng-bind-html=\"" + field.ngBindHtml + "\" " : "";
                html += (field.columnClick) ? "ng-click=\"" + field.columnClick + "\" " : "";
                html += (field.awEllipsis) ? "aw-ellipsis " : "";
                html += ">\n";

                // Add ngShow
                html += (field.ngShow) ? "<span " + Attr(field, 'ngShow') + ">" : "";

                //Add ngHide
                //html += (field.ngHide) ? "<span " + Attr(field, 'ngHide') + ">" : "";

                // Badge
                if (options.mode !== 'lookup' && (field.badges || (field.badgeIcon && field.badgePlacement && field.badgePlacement === 'left'))) {
                    html += Badge(field);
                }

                // Add collapse/expand icon  --used on job_events page
                if (list.hasChildren && field.hasChildren) {
                    html += "<div class=\"level level-{{ " + list.iterator + ".event_level }}\"><a href=\"\" ng-click=\"toggle(" +
                        list.iterator + ".id)\"> " +
                        "<i class=\"{{ " + list.iterator + ".ngicon }}\"></i></a></div>";
                }

                if (list.name === 'groups') {
                    html += "<div class=\"group-name\">";
                }
                if (list.name === 'hosts') {
                    html += "<div class=\"host-name\">";
                }

                // Start the Link
                if ((field.key || field.link || field.linkTo || field.ngClick || field.ngHref || field.awToolTip || field.awPopOver) &&
                    options.mode !== 'lookup' && options.mode !== 'select' && !field.noLink && !field.ngBindHtml) {
                    if(field.noLink === true){
                        // provide an override here in case we want key=true for sorting purposes but don't want links -- see: portal mode,
                    }
                    else if (field.icons) {
                        field.icons.forEach(function(icon, idx) {
                            var key, i = field.icons[idx];
                            for (key in i) {
                                field[key] = i[key];
                            }
                            html += BuildLink({
                                list: list,
                                field: field,
                                fld: fld,
                                base: base
                            }) + ' ';
                        });
                    }
                    else if(field.smartStatus){
                      html += '<aw-smart-status></aw-smart-status>';
                    }
                    else {
                        html += BuildLink({
                            list: list,
                            field: field,
                            fld: fld,
                            base: base
                        });
                    }
                }
                else {
                    // Add icon:
                    if (field.ngShowIcon) {
                        html += "<i ng-show=\"" + field.ngShowIcon + "\" class=\"" + field.icon + "\"></i> ";
                    } else if (field.icon) {
                        html += Icon(field.icon) + " ";
                    }
                    // Add data binds
                    if (!field.ngBindHtml && !field.iconOnly && (field.showValue === undefined || field.showValue === true)) {
                        if (field.ngBind) {
                            html += "{{ " + field.ngBind;
                        } else {
                            html += "{{ " + list.iterator + "." + fld;
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
                }

                if (list.name === 'hosts' || list.name === 'groups') {
                    html += "</div>";
                }

                // close ngShow
                html += (field.ngShow) ? "</span>" : "";

                //close ngHide
                //html += (field.ngHide) ? "</span>" : "";

                // Specific to Job Events page -showing event detail/results
                html += (field.appendHTML) ? "<div ng-show=\"" + field.appendHTML + " !== null\" " +
                    "ng-bind-html=\"" + field.appendHTML + "\" " +
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
            ngHide = params.ngHide,
            idx = params.idx,
            bind = params.bind,
            html = '';

        html += "<div class=\"panel-group collapsible-help\" ";
        html += (show) ? "ng-show=\"" + show + "\" " : "";
        html += (ngHide) ? "ng-hide=\"" + ngHide  + "\" " : "";
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
        html += (bind) ? "ng-bind-html=\"" + bind + "\" " : "";
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
            i, html = '',
            modifier,
            searchWidgets = (params.searchWidgets) ? params.searchWidgets : 1,
            sortedKeys;

        function addSearchFields(idx) {
            var html = '';
            sortedKeys = Object.keys(form.fields).sort();
            sortedKeys.forEach(function(fld) {
                if ((form.fields[fld].searchable === undefined || form.fields[fld].searchable === true) &&
                    (((form.fields[fld].searchWidget === undefined || form.fields[fld].searchWidget === 1) && idx === 1) ||
                    (form.fields[fld].searchWidget === idx))) {
                    html += "<li><a href=\"\" ng-click=\"setSearchField('" + iterator + "','";
                    html += fld + "','";
                    if (form.fields[fld].searchLabel) {
                        html += form.fields[fld].searchLabel + "', " + idx + ")\">" +
                            form.fields[fld].searchLabel + "</a></li>\n";
                    } else {
                        html += form.fields[fld].label.replace(/<br \/>/g, ' ') + "', " + idx + ")\">" +
                            form.fields[fld].label.replace(/<br \/>/g, ' ') + "</a></li>\n";
                    }
                }
            });
            return html;
        }

        for (i = 1; i <= searchWidgets; i++) {
            modifier = (i === 1) ? '' : i;

            if (includeSize) {
                html += "<div class=\"";
                html += (size) ? size : "col-lg-4 col-md-6 col-sm-8 col-xs-9";
                html += "\" id=\"search-widget-container" + modifier + "\">\n";
            }

            html += "<div class=\"input-group input-group-sm";
            html += "\">\n";
            html += "<div class=\"input-group-btn dropdown\">\n";
            html += "<button type=\"button\" ";
            html += "id=\"search_field_ddown\" ";
            html += "class=\"btn btn-default dropdown-toggle\" data-toggle=\"dropdown\"";
            html += ">\n";
            html += "<span ng-bind=\"" + iterator + "SearchFieldLabel" + modifier + "\"></span>\n";
            html += "<span class=\"caret\"></span>\n";
            html += "</button>\n";
            html += "<ul class=\"dropdown-menu\" id=\"" + iterator + "SearchDropdown" + modifier + "\">\n";
            html += addSearchFields(i);
            html += "</ul>\n";
            html += "</div><!-- input-group-btn -->\n";

            html += "<select id=\"search_value_select\" ng-show=\"" + iterator + "SelectShow" + modifier + "\" " +
                "ng-model=\"" + iterator + "SearchSelectValue" + modifier + "\" ng-change=\"search('" + iterator + "')\" ";
            html += "ng-options=\"c.name for c in " + iterator + "SearchSelectOpts track by c.value" + modifier + "\" class=\"form-control search-select";
            html += "\"></select>\n";


            html += "<input id=\"search_value_input\" type=\"text\" ng-hide=\"" + iterator + "SelectShow" + modifier + " || " +
                iterator + "InputHide" + modifier + "\" " +
                "class=\"form-control\" ng-model=\"" + iterator + "SearchValue" + modifier + "\" " +
                "aw-placeholder=\"" + iterator + "SearchPlaceholder" + modifier + "\" type=\"text\" ng-disabled=\"" + iterator +
                "InputDisable" + modifier + " || " + iterator + "HoldInput" + modifier + "\" ng-keypress=\"startSearch($event,'" +
                iterator + "')\">\n";

            // Reset button for drop-down
            html += "<div class=\"input-group-btn\" ng-show=\"" + iterator + "SelectShow" + modifier + "\" >\n";
            html += "<button type=\"button\" class=\"btn btn-default btn-small\" id=\"search-reset-button\" ng-click=\"resetSearch('" + iterator + "')\" " +
                "aw-tool-tip=\"Clear the search\" data-placement=\"top\"><i class=\"fa fa-times\"></i></button>\n";
            html += "</div><!-- input-group-btn -->\n";

            html += "</div><!-- input-group -->\n";

            html += "<a class=\"search-reset-start\" id=\"search-reset-button\" ng-click=\"resetSearch('" + iterator + "')\"" +
                "ng-hide=\"" + iterator + "SelectShow" + modifier + " || " + iterator + "InputHide" + modifier + " || " +
                iterator + "ShowStartBtn" + modifier + " || " +
                iterator + "HideAllStartBtn" + modifier + "\"" +
                "><i class=\"fa fa-times\"></i></a>\n";

            html += "<a class=\"search-reset-start\" id=\"search-submit-button\" ng-click=\"search('" + iterator + "')\"" +
                "ng-hide=\"" + iterator + "SelectShow" + modifier + " || " + iterator + "InputHide" + modifier + " || " +
                "!" + iterator + "ShowStartBtn" + modifier + " || " +
                iterator + "HideAllStartBtn" + modifier + "\"" +
                "><i class=\"fa fa-search\"></i></a>\n";

            html += "<div id=\"search-widget-spacer\" ng-show=\"" + iterator + "SelectShow" + modifier + "\"></div>\n";

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
            html += "<div id=\"" + iterator + "-pagination\" class=\"row page-row\">\n";
            html += "<div class=\"col-lg-8 col-md-8\">\n";
            html += "<ul id=\"pagination-links\" class=\"pagination\" ng-hide=\"" + iterator + "HidePaginator || " + iterator + "_num_pages <= 1\">\n";
            html += "<li ng-hide=\"" + iterator + "_page -5 <= 1 \"><a href id=\"first-page-set\" ng-click=\"getPage(1,'" + set + "','" + iterator + "')\">" +
                "<i class=\"fa fa-angle-double-left\"></i></a></li>\n";

            html += "<li ng-hide=\"" + iterator + "_page -1 <= 0\"><a href " +
                "id=\"previous-page\" ng-click=\"getPage(" + iterator + "_page - 1,'" + set + "','" + iterator + "')\">" +
                "<i class=\"fa fa-angle-left\"></i></a></li>\n";

            // html += "<li ng-repeat=\"page in " + iterator + "_page_range\" ng-class=\"pageIsActive(page,'" + iterator + "')\">" +
            //     "<a href id=\"{{ 'link-to-page-' + page }}\" ng-click=\"getPage(page,'" + set + "','" + iterator + "')\">{{ page }}</a></li>\n";
            html += "<li ng-repeat=\"page in " + iterator + "_page_range\" ng-class=\"pageIsActive(page,'" + iterator + "')\">" +
                "<a href id=\"{{ 'page-' + page }}\" ng-click=\"getPage(page,'" + set + "','" + iterator + "')\">{{ page }}</a></li>\n";

            html += "<li ng-hide=\"" + iterator + "_page + 1 > " + iterator + "_num_pages\"><a href id=\"next-page\"  ng-click=\"" +
                "getPage(" + iterator + "_page + 1,'" + set + "','" + iterator + "')\"><i class=\"fa fa-angle-right\"></i></a></li>\n";

            html += "<li ng-hide=\"" + iterator + "_page +4 >= " + iterator + "_num_pages\"><a href id=\"last-page-set\"  ng-click=\"" +
                "getPage(" + iterator + "_num_pages,'" + set + "','" + iterator + "')\"><i class=\"fa fa-angle-double-right\"></i></a></li>\n";
            html += "</ul>\n";
            html += "</div>\n";
            html += "<div class=\"col-lg-4 col-md-4\" ng-hide=\"" + iterator + "_mode == 'lookup'\">\n";
            html += "<div id=\"pagination-labels\" class=\"page-label\">\n";
            html += "Page <span id=\"current-page\">{{ " + iterator + "_page }}</span> of <span id=\"total-pages\">{{ " + iterator + "_num_pages }}</span> (<span id=\"total-items\">{{ " + iterator + "_total_rows | number:0 }}</span> items)";
            html += "</div>\n";
            html += "</div>\n";
            html += "</div>\n";

            return html;
        };
    }
]);
