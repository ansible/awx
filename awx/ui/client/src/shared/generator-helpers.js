/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

  /**
 *  @ngdoc function
 *  @name shared.function:generator-helpers
 *  @description
 * GeneratorHelpers
 *
 * Functions shared between FormGenerator and ListGenerator
 *
 */
 import systemStatus from '../smart-status/main';


export default
angular.module('GeneratorHelpers', [systemStatus.name])

.factory('Attr', function () {
    return function (obj, key, fld) {
        var i, s, result,
            value = (typeof obj[key] === "string") ? obj[key].replace(/[\"]/g, '&quot;').replace(/[\']/g, '&apos;') : obj[key];

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
            // In the cases where we specify trueValue and falseValue,
            // the boolean value from the API is getting converted to
            // a string. After upgrading to angular 1.4, we need to quote
            // the ng-true-value and ng-false-value values so we compare
            // them appropriately.
            //
            case 'trueValue':
                result = "ng-true-value=\"'" + value + "'\" ";
                break;
            case 'falseValue':
                result = "ng-false-value=\"'" + value + "'\" ";
                break;
            case 'awPopOver':
                // construct the entire help link
                result = "<a aria-label=\"{{'Show help text' | translate}}\" id=\"awp-" + fld + "\" href=\"\" aw-pop-over=\'" + value + "\' ";
                result += (obj.dataPlacement) ? "data-placement=\"" + obj.dataPlacement + "\" " : "";
                result += (obj.dataContainer) ? "data-container=\"" + obj.dataContainer + "\" " : "";
                result += (obj.dataTitle) ? "over-title=\"" + obj.dataTitle + "\" " : "";
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
            case 'awLookupWhen':
                result = "ng-attr-awlookup=\"" + value + "\" ";
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
            case 'system_tracking':
                icon = "fa-crosshairs";
                break;
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
            case 'source_update':
                icon = 'fa-refresh';
                break;
            case 'inventory_update':
                icon = 'fa-refresh';
                break;
            case 'scm_update':
                icon = 'fa-refresh';
                break;
            case 'run':
            case 'rerun':
            case 'submit':
                icon = 'icon-launch';
                break;
            case 'launch':
                icon = 'icon-launch';
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
            case 'question_cancel':
                icon = 'fa-times';
                break;
            case 'job_details':
                icon = 'fa-list-ul';
                break;
            case 'test':
                icon = 'fa-bell-o';
                break;
            case 'copy':
                icon = "fa-copy";
                break;
            case 'insights':
                icon = "fa-info";
                break;
            case 'network':
                icon = "fa-sitemap";
                break;
            case 'cancel':
                icon = "fa-minus-circle";
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
                html = '';
                html = "<td class=\"" + fld + "-column";
                html += (field.columnClass) ? " " + field.columnClass : "";
                html += "\">\n";
                if (!field.noLink){
                    html += "<a ng-href=\"" + field.ngHref + "\" aw-tool-tip=\"" + field.awToolTip + "\"";
                    html += (field.dataPlacement) ? " data-placement=\"" + field.dataPlacement + "\"" : "";
                    html += ">";
                }
                html += "<span class=\"badge List-titleBadge\"";
                html += " aw-tool-tip=\"" + field.awToolTip + "\"";
                html += (field.dataPlacement) ? " data-placement=\"" + field.dataPlacement + "\"" : "";
                html += (field['class']) ? " " + field['class'] : "";
                html += (field.ngHide) ? "\" ng-hide=\"" + field.ngHide : "";
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
            }
            else if(field.badgeCustom === true){
                html += field.badgeIcon;
            }
            else {
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
        } else if (field.uiSref) {
            html += "<a ui-sref=\"" + field.uiSref + "\" ";
        } else if (field.link || (field.key && (field.link === undefined || field.link))) {
            html += "<a href=\"#/" + base + "/{{" + list.iterator + ".id }}\" ";
        } else {
            html += "<a href=\"\"";
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
        if (field.awPopOver) {
            html += "aw-pop-over=\"" + field.awPopOver + "\" ";
            html += (field.dataPlacement) ? "data-placement=\"" + field.dataPlacement + "\" " : "";
            html += (field.dataTitle) ? "over-title=\"" + field.dataTitle + "\" " : "";
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
        if (field.alt_text) {
            html += " &nbsp" + field.alt_text;
        }
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

.factory('Column', ['i18n', 'Attr', 'Icon', 'DropDown', 'Badge', 'BadgeCount', 'BuildLink', 'Template',
    function (i18n, Attr, Icon, DropDown, Badge, BadgeCount, BuildLink, Template) {
        return function (params) {
            var list = params.list,
                fld = params.fld,
                options = params.options,
                base = params.base,
                field = params.field ? params.field : list.fields[fld],
                html = '';

            field.columnClass = field.columnClass ? "List-tableCell " + field.columnClass : "List-tableCell";
            const classList = Attr(field, 'columnClass');

            if (field.type !== undefined && field.type === 'DropDown') {
                html = DropDown(params);
            } else if (field.type === 'role') {
                html += `
<div ${classList}>
    <role-list delete-target=\"${list.iterator}\" class=\"RoleList\">
    </role-list>
</div>
                `;
            } else if (field.type === 'team_roles') {
                html += `
<div ${classList}>
    <role-list delete-target=\"${list.iterator}\" class=\"RoleList\" team-role-list="true">
    </role-list>
</div>
                `;
            } else if (field.type === 'labels') {
                let showDelete = field.showDelete === undefined ? true : field.showDelete;
                    html += `
<div ${classList}>
    <labels-list class=\"LabelList\" show-delete="${showDelete}">
    </labels-list>
</div>
                    `;
            } else if (field.type === 'related_groups') {
                let showDelete = field.showDelete === undefined ? true : field.showDelete;
                    html += `
<div ${classList}>
    <related-groups-labels-list class=\"LabelList\" show-delete="${showDelete}">
    </related-groups-labels-list>
</div>
                    `;
            } else if (field.type === 'owners') {
                html += `
<div ${classList}>
    <owner-list></owner-list>
</div>
                `;
            } else if (field.type === 'revision') {
                html += `
                <div ${classList}>
                    <at-truncate ng-if="project.scm_revision" string="{{project.scm_revision}}" maxLength="7"></at-truncate>
                </div>`;
            } else if (field.type === 'badgeCount') {
                html = BadgeCount(params);
            } else if (field.type === 'badgeOnly') {
                html = Badge(field);
            } else if (field.type === 'template') {
                html = Template(field);
            } else if (field.type === 'toggle') {
                const ngIf = field.ngIf ? `ng-if="${field.ngIf}"` : '';
                html += `
                    <div class="atSwitch-listTableCell ${field['class']} ${field.columnClass}" ${ngIf}>
                        <at-switch on-toggle="${field.ngClick}" switch-on="${"flag" in field} ? ${list.iterator}.${field.flag} : ${list.iterator}.enabled" switch-disabled="${"ngDisabled" in field} ? ${field.ngDisabled} : false" tooltip-string="${field.awToolTip}" tooltip-placement="${field.dataPlacement ? field.dataPlacement : 'right'}" tooltip-watch="${field.dataTipWatch}"></at-switch>
                    </div>
                `;
            } else if (field.type === 'invalid') {
                html += `<div class='List-tableRow--invalid'><div class='List-tableRow--invalidBar' ng-show="${field.ngShow}"`;
                html += `aw-tool-tip="${field.awToolTip}" data-placement=${field.dataPlacement}>`;
                html += "<i class='fa fa-exclamation'></i>";
                html += "</div></div>";
            } else {
                html += "<div class=\"List-tableCell " + fld + "-column";
                html += (field['class']) ? " " + field['class'] : "";
                if (options.mode === 'lookup' && field.modalColumnClass) {
                    html += " " + field.modalColumnClass;
                }
                else if (field.columnClass) {
                    html += " " + field.columnClass;
                }
                html += "\" ";
                html += field.columnNgClass ? " ng-class=\"" + field.columnNgClass + "\"": "";
                if(options.mode === 'lookup' || options.mode === 'select') {
                    if (options.input_type === "radio") {
                        html += " ng-click=\"toggle_row(" + list.iterator + ")\"";
                    } else {
                        html += " ng-click=\"toggle_" + list.iterator + "(" + list.iterator + ", true)\"";
                    }
                }
                html += (field.columnShow) ? Attr(field, 'columnShow') : "";
                html += (field.ngBindHtml) ? "ng-bind-html=\"" + field.ngBindHtml + "\" " : "";
                html += (field.columnClick) ? "ng-click=\"" + field.columnClick + "\" " : "";
                html += (field.awEllipsis) ? "aw-ellipsis " : "";
                html += ">\n";

                if(field.template) {
                    html += field.template;
                }
                else {

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
                    if ((field.key || field.link || field.linkTo || field.ngClick || field.ngHref || field.uiSref || field.awToolTip || field.awPopOver) &&
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
                                    base: field.linkBase || base
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
                                base: field.linkBase || base
                            });
                        }
                    }
                    else {
                        if(field.simpleTip) {
                            html += `<span aw-tool-tip="${field.simpleTip.awToolTip}" data-placement=${field.simpleTip.dataPlacement}>`;
                        }
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
                        if(field.simpleTip) {
                            html += `</span>`;
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

                    // Field Tag
                    if (field.tag) {
                        html += `<span class="at-RowItem-tag" ng-show="${field.showTag}">
                                    ${field.tag}
                                </span>`;
                    }
                }
                html += "</div>";
            }
            return html;
        };
    }
])

.factory('ActionButton', function () {
    return function (options) {

        var html = '';
        html += '<button ';
        html += (options.mode) ? "mode=\"" + options.mode + "\" " : "";
        html += (options.awToolTip) ? "aw-tool-tip=\"" + options.awToolTip + "\" " : "";
        html += (options.dataTipWatch) ? "data-tip-watch=\"" + options.dataTipWatch + "\" " : "";
        html += (options.dataPlacement) ? "data-placement=\"" + options.dataPlacement + "\" " : "";
        html += (options.dataContainer) ? "data-container=\"" + options.dataContainer + "\" " : "";
        html += (options.actionClass) ? "class=\"" + options.actionClass + "\" " : "";
        html += (options.actionId) ? "id=\"" + options.actionId + "\" " : "";
        html += (options.dataTitle) ? "data-title=\"" + options.dataTitle + "\" " : "";
        html += (options.ngDisabled) ? "ng-disabled=\"" + options.ngDisabled + "\" " : "";
        html += (options.ngClick) ? "ng-click=\"$eval(" + options.ngClick + ")\" " : "";
        html += (options.ngShow) ? "ng-show=\"" + options.ngShow + "\" " : "";
        html += (options.ngHide) ? "ng-hide=\"" + options.ngHide + "\" " : "";
        html += '>';
        html += '<span translate>';
        html += (options.buttonContent) ? options.buttonContent : "";
        html += '</span>';
        html += '</button>';

        return html;

    };
})

.factory('MessageBar', function() {
    return function(options) {
        let html = '';
        if (_.has(options, 'messageBar')) {
            let { messageBar } = options;
            html += `<div class="Section-messageBar" ng-show="${messageBar.ngShow}">
                <i class="Section-messageBar-warning fa fa-warning"></i>
                <span class="Section-messageBar-text">${messageBar.message}</span>
            </div>`;
        }
        return html;
    };
});
