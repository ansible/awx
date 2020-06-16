/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 *  @ngdoc function
 *  @name shared.function:list-generator
 *  @description
 * #ListGenerator
 *
 * Use GenerateList.inject(list_object, { key:value }) to generate HTML from a list object and inject it into the DOM. Returns the $scope of the new list.
 *
 * Pass in a list object and a JSON object of key:value parameters. List objects are found in lists/*.js. Possible parameters include:
 *
 * | Parameter | Required | Description |
 * | --------- | -------- | ----------- |
 * | activityStream | | Used in widgets/stream.js to create the list contained within the activity stream widget. |
 * | hdr | | Deprecated. Was used when list generator created the lookup dialog. This was moved to helpers/Lookup.js. |
 * | id | | DOM element ID attribute value. Use to inject the list into a custom DOM element. Otherwise, the HTML for a list will be injected into the DOM element with an ID attribute of 'htmlTemplate'. |
 * | listSize  | | Bootstrap size class to apply to the grid column containing the action buttons, which generally appears to the right of the search widget. Defaults to 'col-lg-8 col-md-6 col-sm-4 col-xs-3'. |
 * | mode | Yes | One of 'edit', 'lookup', 'select', or 'summary'. Generally this will be 'edit'. helpers/Lookup.js uses 'lookup' to generate the lookup dialog. The 'select' option is used in certain controllers when multiple objects are being added to a parent object. For example, building a select list of Users that can be added to an Oranization. 'summary' is no longer used. |
 * | scope |  | If the HTML will be injected into the DOM by list generator, pass in an optional $scope to be used in conjuction with $compile. The list will be associated with the scope value. Otherwise, the scope of the DOM element will be fetched passed to $compile. |
 * | showSearch | | true or false. Set to false, if the search widget should not be included in the generated HTML. |
 *
 * #HTML only
 *
 * Use the buildHTML() method to get a string containing the generated HTML for a list object. buldHTML() expects the same parameters as the inject method. For example:
 * ```
 *     var html = GenerateList.buildHTML({
 *         mode: 'edit',
 *         showSearch: false
 *     });
 * ```
 *
 * #List Objects
 *
 * List objects are found in lists/*.js. Any API endpoint that returns a collection or array is represented with a list object. Examples inlcude Organizations, Credentials, Inventories, etc.
 * A list can have the following attributes:
 *
 * | Attribute | Description |
 * | --------- | ----------- |
 * | index | true or false. If false, the index column, which adds a sequential number to each table row starting with 1, will not be added to the table. |
 * | iterator | String containing a descriptive name of a single row in the collection - inventory, organization, credential, etc. Used to generate name and ID attributes in the list HTML. |
 * | name | Name of the collection. Generally matches the endpoint name - inventories, organizations, etc. Will match the $scope variable containing the array of rows comprising the collection. |
 * | selectTitle | Descriptive title used when mode is 'select'. |
 * | selectInstructions | Text and HTML used to create popover for help button when mode is 'select'. |
 * | editTitle | Descriptive title used when mode is 'edit'. |
 *
 * ##Fields
 *
 * A list contains a fields object. Each column in the list is defined as a separate object within the fields object. A field definition may contain the following attributes:
 *
 * | Attribute | Description |
 * | --------- | ----------- |
 * | columnClass | String of CSS class names to add to the &lt;td&gt; elemnts of the table column. |
 * | columnClick | Adds an ng-click directive to the &lt;td&gt; element. |
 * | excludeModal | true or false. If false, the field will not be included in the generated HTML when the mode is 'lookup' |
 * | key | true or false. If set to true, helpers/search.js will use the field name as the default sort order when generating the API request. |
 * | noLink | true or false. If set to true this will override any 'key', 'linkTo', 'ngClick', or other option that would cause the field to be a link. Used in portal mode and custom inv. script. |
 * | label | Text string used as the column header text. |
 * | linkTo | Wraps the field value with an &lt;a&gt; element. Set to the value of the href attribute. |
 * | ngClick | Wraps the field value with an &lt;a&gt; and adds the ng-click directive. Set to the JS expression that ng-click will evaluate. |
 * | nosort | true or false. Setting to false removes the ability to sort the table by the column. |
 * | searchOnly | true or false. Set to true if the field should be included in the search widget but not included as a column in the generated HTML &lt;table&gt;. |
 * | searchOptions | Array of { name: 'Descriptive Name', value: 'api_value' } objects used to generate &lt;options&gt; for the &lt;select&gt; when searchType is 'select'. |
 * | searchType | One of the available search types defined in helpers/search.js. |
 * | sourceField | Name of the attribute within summary_fields.<source_model> that the field maps to in the API response object. Used in conjunction with sourceModel. |
 * | sourceModel | Name of the summary_fields object that the field maps to in the API response object. |
 *
 * ##Field Actions
 *
 * A list contains a fieldActions object. Each icon found in the Actions column is defined as an object within the fieldActions object. fieldActions can have a columnClass attribute,
 * which may contain a string of CSS class names to add to the action &lt;td&gt; element. It may also contain a label attribute, which can be set to false to suppress the Actions column header.
 *
 * Field action items can have the following attributes:
 *
 * | Attribute | Description |
 * | --------- | ----------- |
 * | actionclass | Set to a string containing any CSS classes to add to the button. |
 * | awToolTip | Adds the aw-tool-tip directive. Set to the value of the HTML or text to dislay in the tooltip. |
 * | buttonContent | String containing button content.  HTML is accepted in this string. |
 * | dataPlacement | Set to the Bootstrip tooltip placement - right, left, top, bottom, etc. |
 * | dataTipWatch | Set to the $scope variable that contains the text and HTML to display in the tooltip. A $scope.$watch will be added to the variable so that anytime its value changes the tooltip will change. |
 * | mode | One of 'all' or 'edit'. Will generally be 'all'. Note that field actions are not displayed when the list is in 'lookup' mode. |
 * | ngClass | Adds the ng-class directive. Set to the JS expression that ng-class will evaluate. |
 * | ngShow | Adds the ng-show directive. Set to the JS expression that ng-show will evaluate. |
 *
 * ##Actions
 *
 * A list can contain an actions object. The actions object contains an object for each action button displayed in the top-right corner of the list container. An action can have the same
 * attributes as an action defined in fieldAction. Both are actions. Clicking on an action evaluates the JS found in the ngClick attribute. In both cases icon is generated automatically by the SelectIcon() method in js/shared/generator-helpers.js.
 * The real difference is that an &lt;a&gt element is used to generate fieldAction items while a &lt;button&gt; element is used for action items.
 */

import { templateUrl } from '../../shared/template-url/template-url.factory';

export default ['$compile', 'Attr', 'Icon',
    'Column', 'DropDown', 'SelectIcon', 'ActionButton', 'i18n',
    function($compile, Attr, Icon, Column, DropDown,
        SelectIcon, ActionButton, i18n) {
        return {

            setList: function(list) {
                this.list = list;
            },

            setOptions: function(options) {
                this.options = options;
            },

            attr: Attr,

            icon: Icon,

            has: function(key) {
                return (this.form[key] && this.form[key] !== null && this.form[key] !== undefined) ? true : false;
            },

            buildHTML: function(list, options) {
                this.setList(list);
                return this.build(options);
            },

            build: function(options) {
                this.list = options.list;
                this.options = options;

                var html = '',
                    list = this.list,
                    base, action, fld, field_action, fAction, itm;

                if (options.mode !== 'lookup') {
                    // Don't display an empty <div> if there is no listTitle
                    if ((options.title !== false && list.title !== false) && list.listTitle !== undefined) {
                        html += "<div class=\"List-header\" >";
                        html += "<div class=\"List-title\" translate>";
                        if (list.listTitle && options.listTitle !== false) {
                            html += "<div class=\"List-titleText\" translate>" + list.listTitle + "</div>";
                            // We want to show the list title badge by default and only hide it when the list config specifically passes a false flag
                            list.listTitleBadge = (typeof list.listTitleBadge === 'boolean' && list.listTitleBadge === false) ? false : true;
                            if (list.listTitleBadge) {
                                html += `<span class="badge List-titleBadge">{{ ${list.iterator}_dataset.count }}</span>`;
                            }
                        }
                        html += "</div>";
                        if (options.cancelButton === true) {
                            html += "<div class=\"Form-exitHolder\">";
                            html += "<button aria-label=\"{{'Close'|translate}}\" class=\"Form-exit\" ng-click=\"formCancel()\">";
                            html += "<i class=\"fa fa-times-circle\"></i>";
                            html += "</button></div>\n";
                        }
                        html += "</div>";
                    }
                }

                if (options.mode === 'edit' && list.editInstructions) {
                    html += "<div class=\"alert alert-info alert-block\">\n";
                    html += "<button aria-label=\"{{'Close'|translate}}\" type=\"button\" class=\"close\" data-dismiss=\"alert\"><i class=\"fa fa-times-circle\"></i></button>\n";
                    html += "<strong>Hint: </strong>" + list.editInstructions + "\n";
                    html += "</div>\n";
                }

                if (list.multiSelectPreview) {
                    html += "<multi-select-preview selected-rows='" + list.multiSelectPreview.selectedRows + "' available-rows='" + list.multiSelectPreview.availableRows + "'></multi-select-preview>";
                }

                if (options.instructions) {
                    html += "<div class=\"instructions alert alert-info\">" + options.instructions + "</div>\n";
                } else if (list.instructions) {
                    html += "<div class=\"instructions alert alert-info\">" + list.instructions + "</div>\n";
                }

                if (options.mode !== 'lookup' && (list.well === undefined || list.well)) {
                    html += `<div class="${list.name}List `; //List-well">`;
                    html += (!list.wellOverride) ? "List-well" : "";
                    html += `">`;
                    // List actions
                    html += "<div class=\"";
                    html += (list.actionHolderClass) ? list.actionHolderClass : "List-actionHolder";
                    html += "\">";
                    html += "<div class=\"List-actions\">";
                    html += `<div ng-include="'${templateUrl('shared/list-generator/list-actions')}'" class="List-actionsInner">`;

                    for (action in list.actions) {
                        list.actions[action] = _.defaults(list.actions[action], { dataPlacement: "top" });
                    }

                    html += "</div>";
                    if (list.toolbarAuxAction) {
                        html += `<div class="List-auxAction">${list.toolbarAuxAction}</div>`;
                    }
                    html += "\n</div>";
                    html += "</div>";
                    // End list actions
                }

                html += (list.searchRowActions) ? "<div class='row'><div class=\"col-lg-8 col-md-8 col-sm-8 col-xs-12\">" : "";
                if (options.showSearch === undefined || options.showSearch === true) {
                    let singleSearchParam = list.singleSearchParam && list.singleSearchParam.param ? `single-search-param="${list.singleSearchParam.param}"` : '';
                    html += `
                    <div ng-hide="!${list.alwaysShowSearch} && ${list.name}.length === 0 && (searchTags | isEmpty)">
                        <smart-search
                            django-model="${list.name}"
                            ${singleSearchParam}
                            base-path="${list.basePath || list.name}"
                            iterator="${list.iterator}"
                            dataset="${list.iterator}_dataset"
                            list="list"
                            collection="${list.name}"
                            default-params="${list.iterator}_default_params"
                            query-set="${list.iterator}_queryset"
                            search-bar-full-width="${list.searchBarFullWidth}"
                            search-tags="searchTags">
                        </smart-search>
                    </div>
                        `;
                }
                if (list.searchRowActions) {
                    html += "</div><div class='col-lg-4 col-md-4 col-sm-4 col-xs-12'>";

                    var actionButtons = "";
                    Object.keys(list.searchRowActions || {})
                        .forEach(act => {
                            actionButtons += ActionButton(list.searchRowActions[act]);
                        });
                    html += `
                            <div class=\"list-actions\">
                                ${actionButtons}
                            </div>
                        `;
                    html += "</div></div>";
                }

                if (options.showSearch !== false) {
                    // Message for when a search returns no results.  This should only get shown after a search is executed with no results.
                    html +=`
                        <div class="row" ng-show="${list.name}.length === 0 && !(searchTags | isEmpty)">
                            <div class="col-lg-12 List-searchNoResults" translate>No records matched your search.</div>
                        </div>
                        `;
                }

                // Show the "no items" box when loading is done and the user isn't actively searching and there are no results
                if (options.showEmptyPanel === undefined || options.showEmptyPanel === true){
                    html += `<div class="${list.emptyListClass || "List-noItems"}" ng-show="${list.name}.length === 0 && (searchTags | isEmpty)">`;
                    html += (list.emptyListText) ? list.emptyListText :  i18n._("PLEASE ADD ITEMS TO THIS LIST");
                    html += "</div>";
                }

                // Add a title and optionally a close button (used on Inventory->Groups)
                if (options.mode !== 'lookup' && list.showTitle) {
                    html += "<div class=\"form-title\">";
                    html += (options.mode === 'edit' || options.mode === 'summary') ? list.editTitle : list.addTitle;
                    html += "</div>\n";
                }

                // table header row
                html += "<div class=\"list-table-container\" ng-show=\"" + list.name + ".length > 0\"";
                html += (list.awCustomScroll) ? " aw-custom-scroll " : "";
                html += ">\n";

                function buildTable() {
                    var extraClasses = list['class'];
                    var multiSelect = list.multiSelect ? 'multi-select-list' : null;
                    var multiSelectExtended = list.multiSelectExtended ? 'true' : 'false';

                    if (options.mode === 'summary') {
                        extraClasses += ' table-summary';
                    }

                    return $('<div>')
                        .attr('id', list.name + '_table')
                        .addClass('List-table')
                        .addClass(extraClasses)
                        .attr('multi-select-list', multiSelect)
                        .attr('is-extended', multiSelectExtended);
                }

                var table = buildTable();
                var innerTable = '';

                if (!options.skipTableHead) {
                    innerTable += this.buildHeader(options);
                }

                const layoutClass = options.mode === 'lookup' ? "List-lookupLayout" : (_.has(list, 'layoutClass') ? list.layoutClass : "List-defaultLayout");

                // table body
                // gotcha: transcluded elements require custom scope linking - binding to $parent models assumes a very rigid DOM hierarchy
                // see: lookup-modal.directive.js for example
                innerTable += options.mode === 'lookup' ? `<div ng-init="selection.${list.iterator} = {id: $parent.${list.iterator}, name: $parent.${list.iterator}_name}">` : `<div>`;

                innerTable += "<div id=\"{{ " + list.iterator + ".id }}\" ";
                innerTable += `class="${layoutClass} List-tableRow ${list.iterator}_class" `;
                innerTable += (list.disableRow) ? " disable-row=\"" + list.disableRow + "\" " : "";
                if(_.has(list, 'disableTooltip')){
                    let { placement, tipWatch } = list.disableTooltip;
                    innerTable += `aw-tool-tip="{{tipWatch}}" data-placement="${placement}" data-tip-watch="${tipWatch}"`;
                }
                innerTable += "ng-repeat=\"" + list.iterator + " in " + list.name;
                innerTable += (list.trackBy) ? " track by " + list.trackBy : "";
                innerTable += (list.orderBy) ? " | orderBy:'" + list.orderBy + "'" : "";
                innerTable += (list.filterBy) ? " | filter: " + list.filterBy : "";
                innerTable += "\">";

                let handleEditStateParams = function(stateParams){
                    let matchingConditions = [];

                    angular.forEach(stateParams, function(stateParam) {
                        matchingConditions.push(`$stateParams['` + stateParam + `'] == ${list.iterator}.id`);
                    });
                    return matchingConditions;
                };

                if (options.mode !== 'lookup') {
                    let activeRowClass;
                    if(list && list.fieldActions && list.fieldActions.edit && list.fieldActions.edit.editStateParams) {
                        let matchingConditions = handleEditStateParams(list.fieldActions.edit.editStateParams);
                        activeRowClass = `ng-class="{'List-tableRow--selected' : ${matchingConditions.join(' || ')}}"`;
                    }
                    else if (list.iterator === 'inventory') {
                        activeRowClass = `ng-class="{'List-tableRow--selected': ($stateParams['${list.iterator}_id'] == ${list.iterator}.id) || ($stateParams['smartinventory_id'] == ${list.iterator}.id)}"`;
                    }
                    else {
                        activeRowClass = `ng-class="{'List-tableRow--selected' : $stateParams['${list.iterator}_id'] == ${list.iterator}.id}"`;
                    }
                    innerTable += `<div ${activeRowClass}></div>`;
                    if (list.multiSelect) {
                        innerTable +=
                            `<div class="List-centerEnd">
                                <select-list-item item="${list.iterator}" disabled="${list.disableRowValue}"></select-list-item>
                            </div>`;
                    }
                    if(list.staticColumns) {
                        angular.forEach(list.staticColumns, function(staticColumn) {
                            innerTable += `<div>`;
                            innerTable += Column({
                                list: list,
                                fld: staticColumn.field,
                                field: staticColumn.content,
                                options: options,
                                base: base
                            });
                            innerTable += `</div>`;
                        });
                    }
                } else {
                    innerTable += `<div class="List-centerEnd select-column">`;
                    if (list.multiSelect) {
                        innerTable += '<select-list-item item=\"' + list.iterator + '\" disabled="'+list.disableRowValue+'"></select-list-item>';
                    } else {
                        if (options.input_type === "radio") { //added by JT so that lookup forms can be either radio inputs or check box inputs
                            innerTable += `<input type="radio" ng-model="${list.iterator}.checked" ng-value="1" ng-false-value="0" name="check_${list.iterator}_{{${list.iterator}.id}}" ng-click="toggle_row(${list.iterator})" ng-disabled="${list.disableRowValue}" />`;
                        }
                        else { // its assumed that options.input_type = checkbox
                            innerTable += "<input type=\"checkbox\" ng-model=\"" + list.iterator + ".checked\" name=\"check_{{" +
                                list.iterator + ".id }}\" ng-click=\"toggle_" + list.iterator + "(" + list.iterator + ", true)\" ng-true-value=\"1\" " +
                                "ng-false-value=\"0\" id=\"check_" + list.iterator + "_{{" + list.iterator + ".id}}\" />";
                        }
                    }
                    innerTable += `</div>`;
                }

                innerTable += `<div class='d-flex h-100' style='min-width: 0;'>`;

                if (list.index) {
                    innerTable += "<div class=\"d-none d-sm-flex index-column List-tableCell\">{{ $index + ((" + list.iterator + "_page - 1) * " + list.iterator + "_page_size) + 1 }}.</div>\n";
                }

                base = (list.base) ? list.base : list.name;
                base = base.replace(/^\//, '');
                for (fld in list.fields) {
                    if ((list.fields[fld].searchOnly === undefined || list.fields[fld].searchOnly === false) &&
                        !(options.mode === 'lookup' && list.fields[fld].excludeModal === true)) {
                        innerTable += Column({
                            list: list,
                            fld: fld,
                            options: options,
                            base: base
                        });
                    }
                }

                if (options.mode === 'select') {
                    if (options.input_type === "radio") { //added by JT so that lookup forms can be either radio inputs or check box inputs
                        innerTable += "<div class=\"List-tableCell\"><input type=\"radio\" ng-model=\"" + list.iterator + ".checked\" name=\"check_{{" +
                            list.iterator + ".id }}\" ng-click=\"toggle_" + list.iterator + "(" + list.iterator + ", true)\" ng-value=\"1\" " +
                            "ng-false-value=\"0\" id=\"check_{{" + list.iterator + ".id}}\" /></div>";
                    } else { // its assumed that options.input_type = checkbox
                        innerTable += "<div class=\"List-tableCell\"><input type=\"checkbox\" ng-model=\"" + list.iterator + ".checked\" name=\"check_{{" +
                            list.iterator + ".id }}\" ng-click=\"toggle_" + list.iterator + "(" + list.iterator + ", true)\" ng-true-value=\"1\" " +
                            "ng-false-value=\"0\" id=\"check_{{" + list.iterator + ".id}}\" /></div>";
                    }
                } else if ((options.mode === 'edit' || options.mode === 'summary') && list.fieldActions) {

                    // Row level actions

                    innerTable += `<div class="List-actionsContainer ${list.fieldActions.columnClass}"><div class="List-actionButtonCell List-tableCell">`;

                    for (field_action in list.fieldActions) {
                        if (field_action !== 'columnClass') {
                            if (list.fieldActions[field_action].type && list.fieldActions[field_action].type === 'DropDown') {
                                innerTable += DropDown({
                                    list: list,
                                    fld: field_action,
                                    options: options,
                                    base: base,
                                    type: 'fieldActions',
                                    td: false
                                });
                            }
                            if (field_action === 'pending_deletion') {
                                innerTable += `<a ng-if='${list.iterator}.pending_deletion'>${i18n._('Pending Delete')}</a>`;
                            } else if (field_action === 'submit') {
                                innerTable += `<at-launch-template template="${list.iterator}" ng-if="${list.iterator}.summary_fields.user_capabilities.start"></at-launch-template>`;
                            } else {
                                // Plug in Dropdown Component
                                if (field_action === 'submit' && list.fieldActions[field_action].relaunch === true) {
                                    innerTable += `<at-relaunch job="${list.iterator}"></at-relaunch>`;
                                } else if (field_action === 'submit' && list.fieldActions[field_action].launch === true) {
                                    innerTable += `<at-launch-template template="${list.iterator}" ng-if="${list.iterator}.summary_fields.user_capabilities.start"></at-launch-template>`;
                                } else {
                                    fAction = list.fieldActions[field_action];
                                    innerTable += "<button id=\"";
                                    innerTable += (fAction.id) ? fAction.id : `${list.iterator}-{{${list.iterator}.id}}-${field_action}-action`;
                                    innerTable += "\" ";
                                    innerTable += (fAction.href) ? "href=\"" + fAction.href + "\" " : "";
                                    innerTable += (fAction.ngHref) ? "ng-href=\"" + fAction.ngHref + "\" " : "";
                                    innerTable += "class=\"List-actionButton ";
                                    innerTable += (field_action === 'delete' || field_action === 'cancel') ? "List-actionButton--delete" : "";
                                    innerTable += "\" ";
                                    if(field_action === 'edit') {
                                        // editStateParams allows us to handle cases where a list might have different types of resources in it.  As a result the edit
                                        // icon might now always point to the same state and differing states may have differing stateParams.  Specifically this occurs
                                        // on the Templates list where editing a workflow job template takes you to a state where the param is workflow_job_template_id.
                                        // You can also edit a Job Template from this list so the stateParam there would be job_template_id.
                                        if(list.fieldActions[field_action].editStateParams) {
                                            let matchingConditions = handleEditStateParams(list.fieldActions[field_action].editStateParams);
                                            innerTable += `ng-class="{'List-editButton--selected' : ${matchingConditions.join(' || ')}}"`;
                                        }
                                        else if (list.iterator === 'inventory') {
                                            innerTable += `ng-class="{'List-editButton--selected': ($stateParams['${list.iterator}_id'] == ${list.iterator}.id) || ($stateParams['smartinventory_id'] == ${list.iterator}.id)}"`;
                                        }
                                        else if (list.iterator === 'host') {
                                            innerTable += `ng-class="{'List-editButton--selected': $stateParams['${list.iterator}_id'] == ${list.iterator}.id && $state.is('inventories.edit.hosts.edit') }"`;
                                        }
                                        else {
                                            innerTable += `ng-class="{'List-editButton--selected' : $stateParams['${list.iterator}_id'] == ${list.iterator}.id}"`;
                                        }
                                    }
                                    innerTable += (fAction.ngDisabled) ? "ng-disabled=\"" + fAction.ngDisabled + "\"" : "";
                                    innerTable += (fAction.awPopOver) ? "aw-pop-over=\"" + fAction.awPopOver + "\" " : "";
                                    innerTable += (fAction.dataPlacement) ? Attr(fAction, 'dataPlacement') : "";
                                    innerTable += (fAction.dataTitle) ? Attr(fAction, 'dataTitle') : "";
                                    for (itm in fAction) {
                                        if (itm !== 'ngHref' && itm !== 'href' && itm !== 'label' && itm !== 'icon' && itm !== 'class' &&
                                            itm !== 'iconClass' && itm !== "dataPlacement" && itm !== "awPopOver" &&
                                            itm !== "dataTitle") {
                                            innerTable += Attr(fAction, itm);
                                        }
                                    }
                                    innerTable += ">";
                                    if (fAction.iconClass) {
                                        innerTable += "<i class=\"" + fAction.iconClass + "\"></i>";
                                    } else {
                                        innerTable += SelectIcon({
                                            action: field_action
                                        });
                                    }
                                    //html += (fAction.label) ? "<span class=\"list-action-label\"> " + list.fieldActions[field_action].label +
                                    //    "</span>" : "";
                                    innerTable += "</button>";
                                }
                            }
                        }
                    }
                    innerTable += "</div></div>\n";
                }

                // might need to wrap this in lookup logic
                // innerTable += "</div>\n";
                // End List
                innerTable += "</div>\n";

                table.html(innerTable);
                html += table.prop('outerHTML');

                html += "</div><!-- table container -->\n";

                if (options.mode === 'select' && (options.selectButton === undefined || options.selectButton)) {
                    html += "<div class=\"navigation-buttons\">\n";
                    html += " <button aria-label=\"{{'Complete your selection'|translate}}\" class=\"btn btn-sm btn-primary pull-right\" id=\"select_btn\" aw-tool-tip=\"Complete your selection\" " +
                        "ng-click=\"finishSelection()\" ng-disabled=\"disableSelectBtn\"><i class=\"fa fa-check\"></i> Select</button>\n";
                    html += "</div>\n";
                }

                if (options.paginate === undefined || options.paginate === true) {
                    let hide_view_per_page = (options.mode === "lookup" || options.hideViewPerPage) ? true : false;
                    html += `<paginate
                    base-path="${list.basePath || list.name}"
                    collection="${list.name}"
                    dataset="${list.iterator}_dataset"
                    iterator="${list.iterator}"
                    query-set="${list.iterator}_queryset"
                    hide-view-per-page="${hide_view_per_page}"`;
                    html += list.maxVisiblePages ? `max-visible-pages="${list.maxVisiblePages}"` : '';
                    html += `></paginate></div>`;
                }

                if (options.mode === 'lookup' && options.lookupMessage) {
                    html = `<div class="Prompt-bodyQuery">${options.lookupMessage}</div>` + html;
                }

                return html;
            },

            buildHeader: function(options) {
                const list = this.list;
                let fld;
                let html = '';

                if (options === undefined) {
                    options = this.options;
                }

                // will probably need some different classes for handling different layouts here
                const layoutClass = options.mode === 'lookup' ? "List-lookupLayout" : (_.has(list, 'layoutClass') ? list.layoutClass : "List-defaultLayout");
                html += `<div class="${layoutClass} List-tableHeaderRow">`;

                html += `<div></div>`;

                if (list.multiSelect) {
                    html += `<div></div>`;
                }

                if (options.mode !== 'lookup' && list.staticColumns) {
                    angular.forEach(list.staticColumns, function() {
                        html += `<div></div>`;
                    });
                }

                html += `<div class='d-flex h-100'>`;

                for (fld in list.fields) {
                    if (options.mode !== 'lookup' || (options.mode === 'lookup' && (fld === 'name' || _.has(list.fields[fld], 'includeModal')))){
                        let customClass = list.fields[fld].columnClass || '';
                        const ngIf = list.fields[fld].ngIf ? `ng-if="${list.fields[fld].ngIf}"` : '';
                        html += `<div
                            ${ngIf}
                            base-path="${list.basePath || list.name}"
                            collection="${list.name}"
                            dataset="${list.iterator}_dataset"
                            column-sort
                            column-field="${list.fields[fld].searchField || fld}"
                            column-iterator="${list.iterator}"
                            column-no-sort="${list.fields[fld].nosort}"
                            column-label="${list.fields[fld].label}"
                            column-custom-class="${customClass}"
                            ng-class="${list.fields[fld].columnNgClass || `{'list-header-noSort': ${list.fields[fld].nosort ? true : false}}`}"
                            query-set="${list.iterator}_queryset">
                        </div>`;
                    }
                }

                if(options.mode === 'edit' && list.fieldActions) {
                    html += `<div id="${list.iterator}-actions-header" class=\"List-tableHeader List-tableHeader--actions actions-column`;
                    html += (list.fieldActions && list.fieldActions.columnClass) ? " " + list.fieldActions.columnClass : "";
                    html += "\" translate>";
                    html += (list.fieldActions.label === undefined || list.fieldActions.label) ? i18n._("Actions") : "";
                    html += "</div>";
                }

                html += "</div>";

                html += `</div>`;

                return html;
            },

            wrapPanel: function(html){
                return `
                <div class="card at-Panel">${html}</div>`;
            },

            insertFormView: function(){
                return `<div ui-view="form"></div>`;
            },

            insertSchedulerView: function(){
                return `<div ui-view="scheduler"></div>`;
            }
        };
    }
];
