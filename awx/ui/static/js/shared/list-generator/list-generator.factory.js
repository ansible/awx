export default ['$location', '$compile', '$rootScope', 'SearchWidget', 'PaginateWidget', 'Attr', 'Icon',
        'Column', 'DropDown', 'NavigationLink', 'SelectIcon', 'Breadcrumbs',
    function ($location, $compile, $rootScope, SearchWidget, PaginateWidget, Attr, Icon, Column, DropDown, NavigationLink,
        SelectIcon, Breadcrumbs) {
            return {

                setList: function (list) {
                    this.list = list;
                },

                setOptions: function(options) {
                    this.options = options;
                },

                attr: Attr,

                icon: Icon,

                has: function (key) {
                    return (this.form[key] && this.form[key] !== null && this.form[key] !== undefined) ? true : false;
                },

                hide: function () {
                    $('#lookup-modal').modal('hide');
                },

                buildHTML: function(list, options) {
                    this.setList(list);
                    return this.build(options);
                },

                inject: function (list, options) {
                    // options.mode = one of edit, select or lookup
                    //
                    // Modes edit and select will inject the list as html into element #htmlTemplate.
                    // 'lookup' mode injects the list html into #lookup-modal-body.
                    //
                    // For options.mode == 'lookup', include the following:
                    //
                    //     hdr: <lookup dialog header>
                    //
                    // Inject into a custom element using options.id: <element id attribute value>
                    // Control breadcrumb creation with options.breadCrumbs: <true | false>
                    //
                    var element;

                    if (options.id) {
                        element = angular.element(document.getElementById(options.id));
                    } else {
                        element = angular.element(document.getElementById('htmlTemplate'));
                    }

                    this.setOptions(options);
                    this.setList(list);
                    element.html(this.build(options)); // Inject the html

                    if (options.prepend) {
                        element.prepend(options.prepend);
                    }

                    if (options.append) {
                        element.append(options.append);
                    }

                    if (options.scope) {
                        this.scope = options.scope;
                    } else {
                        this.scope = element.scope();
                    }

                    this.scope.list = list;
                    this.scope.mode = options.mode;

                    this.scope.performAction = function(action) {
                        this.scope.$eval(action);
                    }.bind(this);

                    this.scope.shouldHideAction = function(options) {
                        return this.scope.$eval(options.ngHide);
                    }.bind(this);
                    this.scope.canShowAction = function(action) {
                        var base = $location.path().replace(/^\//, '').split('/')[0];
                        var inActionMode = options.mode === action.mode || action.mode === 'all';
                        var onScreenForAction =
                            (!options.basePaths) ||
                                (options.basePaths.indexOf(base) > -1);
                        var scopeShow = action.ngShow ? this.scope.$eval(action.ngShow) : true;

                        if (this.scope.shouldHideAction(action)) {
                            return false;
                        } else if (!scopeShow) {
                            return false;
                        } else {
                            return inActionMode && onScreenForAction;
                        }

                        // return _.tap(scopeShow || , function(value) {
                        //     console.log('canShow:', value, options.mode, action.mode, scopeShow);
                        // });
                    }.bind(this);


                    $compile(element)(this.scope);

                    // Reset the scope to prevent displaying old data from our last visit to this list
                    //this.scope[list.name] = null;
                    this.scope[list.iterator] = [];

                    // Remove any lingering tooltip and popover <div> elements
                    $('.tooltip').each(function() {
                        $(this).remove();
                    });

                    $('.popover').each(function() {
                        // remove lingering popover <div>. Seems to be a bug in TB3 RC1
                        $(this).remove();
                    });

                    try {
                        $('#help-modal').empty().dialog('destroy');
                    } catch (e) {
                        //ignore any errors should the dialog not be initialized
                    }

                    /*if (options.mode === 'lookup') {
                        // options should include {hdr: <dialog header>, action: <function...> }
                        this.scope.formModalActionDisabled = false;
                        this.scope.lookupHeader = options.hdr;
                        $('#lookup-modal').modal({
                            backdrop: 'static',
                            keyboard: true
                        });
                        $('#lookup-modal').unbind('hidden.bs.modal');
                        $(document).bind('keydown', function (e) {
                            if (e.keyCode === 27) {
                                $('#lookup-modal').modal('hide');
                            }
                        });
                    }*/

                    return this.scope;
                },

                build: function (options) {
                    //
                    // Generate HTML. Do NOT call this function directly. Called by inject(). Returns an HTML
                    // string to be injected into the current view.
                    //
                    var html = '',
                        list = this.list,
                        base, size, action, fld, cnt, field_action, fAction, itm;

                    if (options.activityStream) {
                        // Breadcrumbs for activity stream widget
                        // Make the links clickable using ng-click function so we can first remove the stream widget
                        // before navigation
                        html += "<div>\n";
                        html += "<ul class=\"ansible-breadcrumb\">\n";
                        html += "<li ng-repeat=\"crumb in breadcrumbs\"><a href=\"\" " + "ng-click=\"closeStream(crumb.path)\">" +
                            "{{ crumb.title }}</a></li>\n";
                        html += "<li class=\"active\"><a href=\"\">";
                        html += list.editTitle;
                        html += "</a></li>\n</ul>\n</div>\n";
                    }
                    //else if (options.mode !== 'lookup' && (options.breadCrumbs === undefined || options.breadCrumbs)) {
                    else if (options.breadCrumbs) {
                        html += Breadcrumbs({
                            list: list,
                            mode: options.mode
                        });
                    }

                    if (options.mode === 'edit' && list.editInstructions) {
                        html += "<div class=\"alert alert-info alert-block\">\n";
                        html += "<button type=\"button\" class=\"close\" data-dismiss=\"alert\">&times;</button>\n";
                        html += "<strong>Hint: </strong>" + list.editInstructions + "\n";
                        html += "</div>\n";
                    }

                    if (options.instructions) {
                        html += "<div class=\"instructions alert alert-info\">" + options.instructions + "</div>\n";
                    }
                    else if (list.instructions) {
                        html += "<div class=\"instructions alert alert-info\">" + list.instructions + "</div>\n";
                    }

                    if (options.mode !== 'lookup' && (list.well === undefined || list.well)) {
                        html += "<div class=\"list-well\">\n";
                    }

                    if (options.activityStream) {
                        // Add a title row
                        html += "<div class=\"row\">\n";
                        html += "<div class=\"col-lg-12\">\n";
                        html += "<h5>{{ streamTitle }}</h5>\n";
                        html += "</div>\n";
                        html += "</div>\n";
                    }

                    if (options.showSearch=== undefined || options.showSearch === true) {
                        html += "<div class=\"row\">\n";
                        if (options.searchSize) {
                            html += SearchWidget({
                                iterator: list.iterator,
                                template: list,
                                mini: true,
                                size: options.searchSize,
                                searchWidgets: list.searchWidgets
                            });
                        } else if (options.mode === 'summary') {
                            html += SearchWidget({
                                iterator: list.iterator,
                                template: list,
                                mini: true,
                                size: 'col-lg-6'
                            });
                        } else if (options.mode === 'lookup' || options.id !== undefined) {
                            html += SearchWidget({
                                iterator: list.iterator,
                                template: list,
                                mini: true,
                                size: 'col-lg-8'
                            });
                        } else {
                            html += SearchWidget({
                                iterator: list.iterator,
                                template: list,
                                mini: true
                            });
                        }

                        if (options.mode !== 'lookup') {
                            //actions
                            html += "<div class=\"";
                            if (options.searchSize && !options.listSize) {
                                // User supplied searchSize, calc the remaining
                                size = parseInt(options.searchSize.replace(/([A-Z]|[a-z]|\-)/g, ''));
                                size = (list.searchWidgets) ? list.searchWidgets * size : size;
                                html += 'col-lg-' + (12 - size);
                            } else if (options.listSize) {
                                html += options.listSize;
                            } else if (options.mode === 'summary') {
                                html += 'col-lg-6';
                            } else if (options.id !== undefined) {
                                html += "col-lg-4";
                            } else {
                                html += "col-lg-8 col-md-6 col-sm-4 col-xs-3";
                            }
                            html += "\">\n";


            html += "<div class=\"list-actions\" ng-include=\"'/static/js/shared/list-generator/list-actions.partial.html'\">\n";

            for (action in list.actions) {
                list.actions[action] =
                    _.defaults(list.actions[action],
                               {    dataPlacement: "top"
                               });
            }

            html += "</div><!-- list-acitons -->\n";

                            html += "</div><!-- list-actions-column -->\n";
                        } else {
                            //lookup
                            html += "<div class=\"col-lg-7\"></div>\n";
                        }
                        html += "</div><!-- row -->\n";
                    }

                    // Add a title and optionally a close button (used on Inventory->Groups)
                    if (options.mode !== 'lookup' && list.showTitle) {
                        html += "<div class=\"form-title\">";
                        html += (options.mode === 'edit' || options.mode === 'summary') ? list.editTitle : list.addTitle;
                        html += "</div>\n";
                    }

                    // table header row
                    html += "<div class=\"list-table-container\"";
                    html += (list.awCustomScroll) ? " aw-custom-scroll " : "";
                    html += ">\n";
                    html += "<table id=\"" + list.name + "_table\" ";
                    html += "class=\"table table-condensed";
                    html += (list['class']) ? " " + list['class'] : "";
                    html += (options.mode !== 'summary' && options.mode !== 'edit' && (options.mode === 'lookup' || options.id)) ?
                        ' table-hover-inverse' : '';
                    html += (list.hover) ? ' table-hover' : '';
                    html += (options.mode === 'summary') ? ' table-summary' : '';
                    html += "\" ";
                    html += ">\n";

                    if (!options.skipTableHead) {
                        html += this.buildHeader(options);
                    }

                    // table body
                    html += "<tbody>\n";
                    html += "<tr ng-class=\"" + list.iterator;
                    html += (options.mode === 'lookup' || options.mode === 'select') ? ".success_class" : ".active_class";
                    html += "\" ";
                    html += "id=\"{{ " + list.iterator + ".id }}\" ";
                    html += "class=\"" + list.iterator + "_class\" ";
                    html += "ng-repeat=\"" + list.iterator + " in " + list.name;
                    html += (list.orderBy) ? " | orderBy:'" + list.orderBy + "'" : "";
                    html += (list.filterBy) ? " | filter: " + list.filterBy : "";
                    html += "\">\n";
                    if (list.index) {
                        html += "<td class=\"index-column hidden-xs\">{{ $index + ((" + list.iterator + "_page - 1) * " + list.iterator + "_page_size) + 1 }}.</td>\n";
                    }
                    cnt = 2;
                    base = (list.base) ? list.base : list.name;
                    base = base.replace(/^\//, '');
                    for (fld in list.fields) {
                        cnt++;
                        if ((list.fields[fld].searchOnly === undefined || list.fields[fld].searchOnly === false) &&
                            !(options.mode === 'lookup' && list.fields[fld].excludeModal === true)) {
                            html += Column({
                                list: list,
                                fld: fld,
                                options: options,
                                base: base
                            });
                        }
                    }

                    if (options.mode === 'select' || options.mode === 'lookup') {
                        if(options.input_type==="radio"){ //added by JT so that lookup forms can be either radio inputs or check box inputs
                            html += "<td><input type=\"radio\" ng-model=\"" + list.iterator + ".checked\" name=\"check_{{" +
                            list.iterator + ".id }}\" ng-click=\"toggle_" + list.iterator + "(" + list.iterator + ".id, true)\" ng-value=\"1\" " +
                            "ng-false-value=\"0\" id=\"check_{{" + list.iterator + ".id}}\" /></td>";
                        }
                        else { // its assumed that options.input_type = checkbox
                            html += "<td><input type=\"checkbox\" ng-model=\"" + list.iterator + ".checked\" name=\"check_{{" +
                            list.iterator + ".id }}\" ng-click=\"toggle_" + list.iterator + "(" + list.iterator + ".id, true)\" ng-true-value=\"1\" " +
                            "ng-false-value=\"0\" id=\"check_{{" + list.iterator + ".id}}\" /></td>";
                        }
                    } else if ((options.mode === 'edit' || options.mode === 'summary') && list.fieldActions) {

                        // Row level actions

                        html += "<td class=\"actions\">";

                        for (field_action in list.fieldActions) {
                            if (field_action !== 'columnClass') {
                                if (list.fieldActions[field_action].type && list.fieldActions[field_action].type === 'DropDown') {
                                    html += DropDown({
                                        list: list,
                                        fld: field_action,
                                        options: options,
                                        base: base,
                                        type: 'fieldActions',
                                        td: false
                                    });
                                } else {
                                    fAction = list.fieldActions[field_action];
                                    html += "<a id=\"";
                                    html += (fAction.id) ? fAction.id : field_action + "-action";
                                    html += "\" ";
                                    html += (fAction.href) ? "href=\"" + fAction.href + "\" " : "";
                                    html += (fAction.ngHref) ? "ng-href=\"" + fAction.ngHref + "\" " : "";
                                    html += (field_action === 'cancel') ? "class=\"cancel red-txt\" " : "";
                                    html += (fAction.awPopOver) ? "aw-pop-over=\"" + fAction.awPopOver + "\" " : "";
                                    html += (fAction.dataPlacement) ? Attr(fAction, 'dataPlacement') : "";
                                    html += (fAction.dataTitle) ? Attr(fAction, 'dataTitle') : "";
                                    for (itm in fAction) {
                                        if (itm !== 'ngHref' && itm !== 'href' && itm !== 'label' && itm !== 'icon' && itm !== 'class' &&
                                            itm !== 'iconClass' && itm !== "dataPlacement" && itm !== "awPopOver" &&
                                            itm !== "dataTitle") {
                                            html += Attr(fAction, itm);
                                        }
                                    }
                                    html += ">";
                                    if (fAction.iconClass) {
                                        html += "<i class=\"" + fAction.iconClass + "\"></i>";
                                    } else {
                                        html += SelectIcon({
                                            action: field_action
                                        });
                                    }
                                    //html += (fAction.label) ? "<span class=\"list-action-label\"> " + list.fieldActions[field_action].label +
                                    //    "</span>" : "";
                                    html += "</a>";
                                }
                            }
                        }
                        html += "</td>\n";
                    }
                    html += "</tr>\n";

                    // Message for when a collection is empty
                    html += "<tr class=\"loading-info\" ng-show=\"" + list.iterator + "Loading == false && " + list.name + ".length == 0\">\n";
                    html += "<td colspan=\"" + cnt + "\"><div class=\"loading-info\">No records matched your search.</div></td>\n";
                    html += "</tr>\n";

                    // Message for loading
                    html += "<tr class=\"loading-info\" ng-show=\"" + list.iterator + "Loading == true\">\n";
                    html += "<td colspan=\"" + cnt + "\"><div class=\"loading-info\">Loading...</div></td>\n";
                    html += "</tr>\n";

                    // End List
                    html += "</tbody>\n";
                    html += "</table>\n";
                    html += "</div><!-- table container -->\n";

                    if (options.mode === 'select' && (options.selectButton === undefined || options.selectButton)) {
                        html += "<div class=\"navigation-buttons\">\n";
                        html += " <button class=\"btn btn-sm btn-primary pull-right\" id=\"select_btn\" aw-tool-tip=\"Complete your selection\" " +
                            "ng-click=\"finishSelection()\" ng-disabled=\"disableSelectBtn\"><i class=\"fa fa-check\"></i> Select</button>\n";
                        html += "</div>\n";
                    }

                    if (options.mode !== 'lookup' && (list.well === undefined || list.well === true)) {
                        html += "</div>\n"; //well
                    }

                    if (options.mode === 'lookup' || (options.id && options.id === "form-modal-body")) {
                        html += PaginateWidget({
                            set: list.name,
                            iterator: list.iterator
                        });
                    } else {
                        html += PaginateWidget({
                            set: list.name,
                            iterator: list.iterator
                        });
                    }

                    return html;
                },

                buildHeader: function(options) {
                    var list = this.list,
                        fld, html;

                    if (options === undefined) {
                        options = this.options;
                    }

                    html = "<thead>\n";
                    html += "<tr>\n";
                    if (list.index) {
                        html += "<th class=\"col-lg-1 col-md-1 col-sm-2 hidden-xs\">#</th>\n";
                    }
                    for (fld in list.fields) {
                        if ((list.fields[fld].searchOnly === undefined || list.fields[fld].searchOnly === false) &&
                            !(options.mode === 'lookup' && list.fields[fld].excludeModal === true)) {
                            html += "<th class=\"list-header";
                            if (options.mode === 'lookup' && list.fields[fld].modalColumnClass) {
                                html += " " + list.fields[fld].modalColumnClass;
                            }
                            else if (list.fields[fld].columnClass) {
                                html += " " + list.fields[fld].columnClass;
                            }
                            html += "\" id=\"" + list.iterator + "-" + fld + "-header\"";
                            html += (list.fields[fld].columnShow) ? " ng-show=\"" + list.fields[fld].columnShow + "\" " : "";
                            html += (list.fields[fld].nosort === undefined || list.fields[fld].nosort !== true) ? " ng-click=\"sort('" + list.iterator + "','" + fld + "')\"" : "";
                            html += ">";
                            html += list.fields[fld].label;
                            if (list.fields[fld].nosort === undefined || list.fields[fld].nosort !== true) {
                                html += " <i class=\"fa ";
                                if (list.fields[fld].key) {
                                    if (list.fields[fld].desc) {
                                        html += "fa-sort-down";
                                    } else {
                                        html += "fa-sort-up";
                                    }
                                } else {
                                    html += "fa-sort";
                                }
                                html += "\"></i></a>";
                            }
                            html += "</th>\n";
                        }
                    }
                    if (options.mode === 'select' || options.mode === 'lookup') {
                        html += "<th class=\"col-lg-1 col-md-1 col-sm-2 col-xs-2\">Select</th>";
                    } else if (options.mode === 'edit' && list.fieldActions) {
                        html += "<th class=\"actions-column";
                        html += (list.fieldActions && list.fieldActions.columnClass) ? " " + list.fieldActions.columnClass : "";
                        html += "\">";
                        html += (list.fieldActions.label === undefined || list.fieldActions.label) ? "Actions" : "";
                        html += "</th>\n";
                    }
                    html += "</tr>\n";
                    html += "</thead>\n";
                    return html;
                }
            };
        }];
