/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 */
  /**
 *  @ngdoc function
 *  @name shared.function:form-generator
 *  @description
 *
 * Generate form HTML from a form object. Form objects are found in /forms.
 *
 * #Generate and Inject Form
 *
 * To generate a form and inject it into the DOM the default method call is:
 *
 * ```
 * GenerateForm.inject(form, { mode: 'edit', related: true, scope: $scope});
 * ```
 * Expects 2 parameters where the first is a reference to a form object, and the second is an object of key/value parameter pairs. Returns the $scope object associated with the generated HTML.
 *
 * Parameters that can be passed:
 *
 * | Parameter | Required | Description |
 * | --------- | -------- | ----------- |
 * | html |  | String of HTML to be injected. Overrides HTML that would otherwise be generated using the form object. (Not sure if this is actually used anywhere.) |
 * | id | | The ID attribute value of the DOM elment that will receive the generated HTML. If provided, form generator will inject the HTML it genertates into the DOM element identified by the string value provided. Do not preceed the value with '#' |
 * | mode | Y | 'add', 'edit' or 'modal'. Use add when creating new data - creating a new orgranization, for example. Use edit when modifying existing data. Modal is deprecated. Use the 'id' option to inject a form into a modal dialog. |
 * | scope |  | Reference to $scope object. Will be passed to $compile and associated with any angular directives contained within the generated HTML. |
 * | breadCrumbs | | true or false. If false, breadcrumbs will not be inlcluded in the generated HTML. |
 * | showButtons | | true or false. If false, buttons defined in the buttons object will not be included in the generated HTML. |
 *
 * #Generate HTML Only
 *
 * To generate the HTML only and not inject it into the DOM use the buildHTML() method:
 *
 * ```
 * GenerateForm.buildHTML(JobVarsPromptForm, { mode: 'edit', modal: true, scope: scope });
 * ```
 *
 * Pass the same parameters as above. Returns a string containing the generated HTML.
 *
 * #Reset Form
 *
 * Call GenerateFrom.reset() to clear user input, remove error messages and return the angular form object back to a pristine state. This is should be called when the user clicks the Reset button.
 *
 * #Form definitions
 *
 * See forms/*.js for examples.
 *
 * The form object can have the following attributes:
 *
 * | Attribute | Description |
 * | --------- | ----------- |
 * | addTitle | Title to use in breadcrumbs when the form mode is 'add' |
 * | breadCrumbs | true or false. Breadcrumbs are included at the top of the page by default. If set to false, breadcrumbs will not be included at the top of the page. |
 * | collapse | true or false. If true, places the form inside a jQueryUI accordion |
 * | collapseMode | 'add' or 'edit'. If the value of the mode parameter passed into .inject() or .buildHTML() matches collapseMode, the &lt;form&gt; will be placed in an accordion. |
 * | collapseOpen |  true or false. If true, the accordion will be open the first time the user views the form, or if no state information is found in local storage for the accordion. Subsequent views will depend on accordion state found in local storage. Each time user opens/closes an accordion the state is saved in local storage. |
 * | collapseOpenFirst | true or false. If true, the collapse will be open everytime the accordion is viewed, regardless of state data found in local storage. |
 * | collapseTitle | Text to use in the &lt;h3&gt; element of the accordion. Typically this will be 'Properties' |
 * | name | Name to give the form object. Used to create the id and name attribute values in the <form> element. |
 * | showActions | true or false. By default actions found in the actions object will be displayed at the top of the page. If set to false, actions will not be displayed. |
 * | twoColumns | true or false. By default fields are placed in a single vertical column following the Basic Example in the [Bootstrap form documentation](http://getbootstrap.com/css/#forms). Set to true for a 2 column layout as seen on the Job Templates detail page.|
 * | well | true or false. If true, wraps the with &lt;div class=&quot;aw-form-well&quot;&gt;&lt;/div&gt; |
 *
 * The form object will contain a fields object to hold the definiation of each field in the form. Attributes on a field object determine the HTML generated for the actual &lt;input&gt; or &lt;textarea&gt; element. Fields can have the following attributes:
 *
 * | Attribute | Description |
 * | --------- | ----------- |
 * | addRequired | true or false. If true, set the required attribute when mode is 'add'. |
 * | awPopOver | Adds aw-pop-over directive. Set to a string containing the text or html to be evaluated by the directive. |
 * | awPopOverWatch | Causes the awPopOver directive to add a $scope.$watch on the specified scop variable. When the value of the variable changes the popover text will be updated with the change. |
 * | awRequiredWhen | Adds aw-required-when directive. Set to an object to be evaluated by the directive. |
 * | capitalize | true or false. If true, apply the 'capitalize' filter to the field. |
 * | class | String cotaining one or more CSS class values. |
 * | column | If the twoColumn option is being used, supply an integer value of 1 or 2 representing the column in which to place the field. 1 places the field in the left column, and 2 places it on the right. |
 * | dataContainer | Used with awPopOver. String providing the containment parameter. |
 * | dataPlacement | Used with awPopOver and awToolTip. String providing the placement parameter (i.e. left, right, top, bottom, etc.). |
 * | dataTitle | Used with awPopOver. String value for the title of the popover. |
 * | default | Default value to place in the field when the form is in 'add' mode. |
 * | defaultText | Default value to put into a select input. |
 * | editRequird | true or false. If true, set the required attribute when mode is 'edit'. |
 * | falseValue | For radio buttons and checkboxes. Value to set the model to when the checkbox or radio button is not selected. |
 * | genMD5 | true or false. If true, places the field in an input group with a button that when clicked replaces the field contents with an MD5 has key. Used with host_config_key on the job templates detail page. |
 * | integer | Adds the integer directive to validate that the value entered is of type integer. Add min and max to supply lower and upper range bounds to the entered value. |
 * | label | Text to use as &lt;label&gt; element for the field |
 * | ngChange | Adds ng-change directive. Set to the JS expression to be evaluated by ng-change. |
 * | ngClick | Adds ng-click directive. Set to the JS expression to be evaluated by ng-click. |
 * | ngHide | Adds ng-hide directive. Set to the JS expression to be evaluated by ng-hide. |
 * | ngShow | Adds ng-show directive. Set to the JS expression to be evaluated by ng-show. |
 * | readonly | Defaults to false. When true the readonly attribute is set, disallowing changes to field content. |
 * | rows | Integer value used to set the row attribute for a textarea. |
 * | sourceModel | Used in conjunction with sourceField when the data for the field is part of the summary_fields object returned by the API. Set to the name of the summary_fields object that contains the field. For example, the job_templates object returned by the API contains summary_fields.inventory. |
 * | sourceField | String containing the summary_field.object.field name from the API summary_field object. For example, if a fields should be associated to the summary_fields.inventory.name, set the sourceModel to 'inventory' and the sourceField to 'name'. |
 * | spinner | true or false. If true, adds aw-spinner directive. Optionally add min and max attributes to control the range of allowed values. |
 * | type | String containing one of the following types defined in buildField: alertblock, hidden, text, password, email, textarea, select, number, checkbox, checkbox_group, radio, radio_group, lookup, custom. |
 * | trueValue | For radio buttons and checkboxes. Value to set the model to when the checkbox or radio button is selected. |
 * | hasShowInputButton (sensitive type only) | This creates a button next to the input that toggles the input as text and password types. |
 * The form object contains a buttons object for defining any buttons to be included in the generated HTML. Generally all forms will have a Reset and a Submit button. If no buttons should be generated define buttons as an empty object, or set the showButtons option to false.
 *
 * The icon used for the button is determined by SelectIcon() found in js/shared/generator-helpers.js.
 *
 * | Attribute | Description |
 * | --------- | ----------- |
 * | class | If the name of the button is reset or save, the class is automatically set to the correct bootstrap btn class for the color. Otherwise, provide a string with any classes to be added to the &lt;button&gt element. |
 * | label | For reset and save buttons the label is automatically set. For other types of buttons set label to the text string that should appear in the button. |
 * | ngClick | Adds the ng-click directive to the button. Set to the JS expression for the ng-click directive to evaluate. |
 * | ngDisabled | Only partially implemented at this point. For buttons other than reset, the ng-disabled directive is always added. The button will be disabled when the form is in an invalid state. |
 *
 * The form object may contain an actions object. The action object can contain one or more button definitions for buttons to appear in the top-right corner of the form. This may include activity stream, refresh, properties, etc. Each button object defined in actions may have the following attributes:
 *
 * | Attribute | Description |
 * | --------- | ----------- |
 * | awToolTip | Text or html to display in the button tooltip. Adds the aw-tool-tip directive. |
 * | class | Optional classes to add to the &lt;button&gt; element. |
 * | dataPlacement | Set the placement attribute of the tooltip - left, right, top, bottom, etc. |
 * | ngClick | Set to the JS expression to be evaluated by the ng-click directive. |
 * | mode | Set to edit or add, depending on which mode the button  |
 * |
 *
 * The form object may contain a related object. The related object contains one or more list objects defining sublists to display in accordions. For example, the Organization form contains a related users list and admins list.
 *
 * As originally conceived sublists were stored inside the form definition without regard to any list definitions found in the lists folder. In other words, lists/Users.js is completely different from the related.users object found in forms/Organizations.js. In reality they
 * are very similar and lists/Users.js should be used to generate the users sublist on the organizations detail page.
 *
 * One approach to making this work and using list definintion inside a from was implemented in forms/JobTemplates.js. In controllers/JobTemplates.js within JobTemplatesEdit() the form object is created by calling the JobTemplateForm() method found in forms/JobTemplates.js. The
 * method injects the SchedulesList and CompletedJobsList into the form object as related sets. Going forward this approach or similar should be used whenever a sublist needs to be added to a form.
 *
 * #Variable editing
 *
 * If the field type is textarea and the name is one of variables, extra_vars, inventory_variables or source_vars, then the parse type radio button group is added. This is the radio button group allowing the user to switch between JSON and YAML.
 *
 * Applying CodeMirror to the text area is handled by ParseTypeChange() found in helpers/Parse.js. Within the controller will be a call to ParseTypeChange that creates the CodeMirror object and sets up the required $scope methods for handles getting, settting and type conversion.
 */

import GeneratorHelpers from './generator-helpers';
import listGenerator from 'tower/shared/list-generator/main';

export default
angular.module('FormGenerator', [GeneratorHelpers.name, 'Utilities', listGenerator.name])

.factory('GenerateForm', ['$rootScope', '$location', '$compile', 'generateList', 'SearchWidget', 'PaginateWidget', 'Attr',
    'Icon', 'Column', 'NavigationLink', 'HelpCollapse', 'DropDown', 'Empty', 'SelectIcon', 'Store',
    function ($rootScope, $location, $compile, GenerateList, SearchWidget, PaginateWidget, Attr, Icon, Column, NavigationLink,
        HelpCollapse, DropDown, Empty, SelectIcon, Store) {
        return {

            setForm: function (form) { this.form = form; },

            attr: Attr,

            icon: Icon,

            accordion_count: 0,

            scope: null,

            has: function (key) {
                return (this.form[key] && this.form[key] !== null && this.form[key] !== undefined) ? true : false;
            },

            inject: function (form, options) {
                //
                // Use to inject the form as html into the view.  View MUST have an ng-bind for 'htmlTemplate'.
                // Returns scope of form.
                //

                var element, fld, set, show, self = this;

                if (options.modal) {
                    if (options.modal_body_id) {
                        element = angular.element(document.getElementById(options.modal_body_id));
                    } else {
                        // use default dialog
                        element = angular.element(document.getElementById('form-modal-body'));
                    }
                } else {
                    if (options.id) {
                        element = angular.element(document.getElementById(options.id));
                    } else {
                        element = angular.element(document.getElementById('htmlTemplate'));
                    }
                }

                this.mode = options.mode;
                this.modal = (options.modal) ? true : false;
                this.setForm(form);

                if (options.html) {
                    element.html(options.html);
                } else {
                    element.html(this.build(options));
                }

                if (options.scope) {
                    this.scope = options.scope;
                } else {
                    this.scope = element.scope();
                }

                if (options.mode) {
                    this.scope.mode = options.mode;
                }

                for (fld in form.fields) {
                    this.scope[fld + '_field'] = form.fields[fld];
                    this.scope[fld + '_field'].name = fld;
                }

                $compile(element)(this.scope);

                if (!options.html) {
                    // Reset the scope to prevent displaying old data from our last visit to this form
                    for (fld in form.fields) {
                        this.scope[fld] = null;
                    }
                    for (set in form.related) {
                        this.scope[set] = null;
                    }
                    if (((!options.modal) && options.related) || this.form.forceListeners) {
                        this.addListeners();
                    }
                    if (options.mode === 'add') {
                        this.applyDefaults();
                    }
                }

                // Remove any lingering tooltip and popover <div> elements
                $('.tooltip').each(function () {
                    $(this).remove();
                });

                $('.popover').each(function () {
                    // remove lingering popover <div>. Seems to be a bug in TB3 RC1
                    $(this).remove();
                });

                // Prepend an asterisk to required field label
                $('.form-control[required], input[type="radio"][required]').each(function () {
                    var label, span;
                    if (Empty($(this).attr('aw-required-when'))) {
                        label = $(this).parent().parent().find('label').first();
                        if ($(this).attr('type') === 'radio') {
                            label = $(this).parent().parent().parent().find('label').first();
                        }
                        if (label.length > 0) {
                            span = label.children('span');
                            if (span.length > 0 && !span.first().hasClass('prepend-asterisk')) {
                                span.first().addClass('prepend-asterisk');
                            } else if (span.length <= 0 && !label.first().hasClass('prepend-asterisk')) {
                                label.first().addClass('prepend-asterisk');
                            }
                        }
                    }
                });

                try {
                    $('#help-modal').empty().dialog('destroy');
                } catch (e) {
                    //ignore any errors should the dialog not be initialized
                }

                if (options.modal) {
                    $rootScope.flashMessage = null;
                    this.scope.formModalActionDisabled = false;
                    this.scope.formModalInfo = false; //Disable info button for default modal
                    if (form) {
                        if (options.modal_title_id) {
                            this.scope[options.modal_title_id] = (options.mode === 'add') ? form.addTitle : form.editTitle;
                        } else {
                            this.scope.formModalHeader = (options.mode === 'add') ? form.addTitle : form.editTitle; //Default title for default modal
                        }
                    }
                    if (options.modal_selector) {
                        $(options.modal_selector).modal({
                            show: true,
                            backdrop: 'static',
                            keyboard: true
                        });
                        $(options.modal_selector).on('shown.bs.modal', function () {
                            $(options.modal_select + ' input:first').focus();
                        });
                        $(options.modal_selector).on('hidden.bs.modal', function () {
                            $('.tooltip').each(function () {
                                // Remove any lingering tooltip and popover <div> elements
                                $(this).remove();
                            });

                            $('.popover').each(function () {
                                // remove lingering popover <div>. Seems to be a bug in TB3 RC1
                                $(this).remove();
                            });
                        });
                    } else {
                        show = (options.show_modal === false) ? false : true;
                        $('#form-modal').modal({
                            show: show,
                            backdrop: 'static',
                            keyboard: true
                        });
                        $('#form-modal').on('shown.bs.modal', function () {
                            $('#form-modal input:first').focus();
                        });
                        $('#form-modal').on('hidden.bs.modal', function () {
                            $('.tooltip').each(function () {
                                // Remove any lingering tooltip and popover <div> elements
                                $(this).remove();
                            });

                            $('.popover').each(function () {
                                // remove lingering popover <div>. Seems to be a bug in TB3 RC1
                                $(this).remove();
                            });
                        });
                    }
                    $(document).bind('keydown', function (e) {
                        if (e.keyCode === 27) {
                            if (options.modal_selector) {
                                $(options.modal_selector).modal('hide');
                            }
                            $('#prompt-modal').modal('hide');
                            $('#form-modal').modal('hide');
                        }
                    });
                }

                if (self.scope && !self.scope.$$phase) {
                    setTimeout(function() {
                        if (self.scope) {
                            self.scope.$digest();
                        }
                    }, 100);
                }

                return self.scope;

            },

            buildHTML: function(form, options) {
                // Get HTML without actually injecting into DOM. Caller is responsible for any injection.
                // Example:
                //   html = GenerateForm.buildHTML(JobVarsPromptForm, { mode: 'edit', modal: true, scope: scope });

                this.mode = options.mode;
                this.modal = (options.modal) ? true : false;
                this.setForm(form);
                return this.build(options);
            },

            applyDefaults: function () {
                for (var fld in this.form.fields) {
                    if (this.form.fields[fld]['default'] || this.form.fields[fld]['default'] === 0) {
                        if (this.form.fields[fld].type === 'select' && this.scope[fld + '_options']) {
                            this.scope[fld] = this.scope[fld + '_options'][this.form.fields[fld]['default']];
                        } else {
                            this.scope[fld] = this.form.fields[fld]['default'];
                        }
                    }
                }
            },

            reset: function () {
                // The form field values cannot be reset with jQuery. Each field is tied to a model, so to clear the field
                // value, you have to clear the model.

                var fld, scope = this.scope,
                    form = this.form;

                if (scope[form.name + '_form']) {
                    scope[form.name + '_form'].$setPristine();
                }

                function resetField(f, fld) {
                    // f is the field object, fld is the key

                    if (f.type === 'checkbox_group') {
                        for (var i = 0; i < f.fields.length; i++) {
                            scope[f.fields[i].name] = '';
                            scope[f.fields[i].name + '_api_error'] = '';
                            scope[form.name + '_form'][f.fields[i].name].$setValidity('apiError', true);
                        }
                    } else {
                        scope[fld] = '';
                        scope[fld + '_api_error'] = '';
                    }
                    if (f.sourceModel) {
                        scope[f.sourceModel + '_' + f.sourceField] = '';
                        scope[f.sourceModel + '_' + f.sourceField + '_api_error'] = '';
                        if (scope[form.name + '_form'][f.sourceModel + '_' + f.sourceField]) {
                            scope[form.name + '_form'][f.sourceModel + '_' + f.sourceField].$setValidity('apiError', true);
                        }
                    }
                    if (f.type === 'lookup' && scope[form.name + '_form'][f.sourceModel + '_' + f.sourceField]) {
                        scope[form.name + '_form'][f.sourceModel + '_' + f.sourceField].$setPristine();
                        scope[form.name + '_form'][f.sourceModel + '_' + f.sourceField].$setValidity('apiError', true);
                    }
                    if (scope[form.name + '_form'][fld]) {
                        scope[form.name + '_form'][fld].$setPristine();
                        scope[form.name + '_form'][fld].$setValidity('apiError', true);
                    }
                    if (f.chkPass && scope[form.name + '_form'][fld]) {
                        if ($AnsibleConfig.password_length) {
                            scope[form.name + '_form'][fld].$setValidity('password_length', true);
                        }
                        if ($AnsibleConfig.password_hasLowercase) {
                            scope[form.name + '_form'][fld].$setValidity('hasLowercase', true);
                        }
                        if ($AnsibleConfig.password_hasUppercase) {
                            scope[form.name + '_form'][fld].$setValidity('hasUppercase', true);
                        }
                        if ($AnsibleConfig.password_hasNumber) {
                            scope[form.name + '_form'][fld].$setValidity('hasNumber', true);
                        }
                        if ($AnsibleConfig.password_hasSymbol) {
                            scope[form.name + '_form'][fld].$setValidity('hasSymbol', true);
                        }
                    }
                    if (f.awPassMatch && scope[form.name + '_form'][fld]) {
                        scope[form.name + '_form'][fld].$setValidity('awpassmatch', true);
                    }
                    if (f.ask) {
                        scope[fld + '_ask'] = false;
                    }
                }

                for (fld in form.fields) {
                    resetField(form.fields[fld], fld);
                }
                if (form.statusFields) {
                    for (fld in form.statusFields) {
                        resetField(form.statusFields[fld], fld);
                    }
                }
                if (this.mode === 'add') {
                    this.applyDefaults();
                }
            },

            checkAutoFill: function(params) {
                var fld, model, newVal, type,
                    scope = (params && params.scope) ? params.scope : this.scope;
                for (fld in this.form.fields) {
                    if (this.form.fields[fld].type === 'text' || this.form.fields[fld].type === 'textarea') {
                        type = (this.form.fields[fld].type === 'text') ? 'input' : 'textarea';
                        model = scope[this.form.name + '_form'][fld];
                        newVal = $(type + '[name="' + fld + '"]').val();
                        if (newVal && model && model.$viewValue !== newVal) {
                            model.$setViewValue(newVal);
                        }
                    }
                }
            },

            addListeners: function () {

                if (this.modal) {
                    $('.jqui-accordion-modal').accordion({
                        collapsible: false,
                        heightStyle: 'content',
                        active: 0
                    });
                } else {
                    // For help collapse, toggle the plus/minus icon
                    this.scope.accordionToggle = function (selector) {
                        $(selector).collapse('toggle');
                        if ($(selector + '-icon').hasClass('fa-minus')) {
                            $(selector + '-icon').removeClass('fa-minus').addClass('fa-plus');
                        } else {
                            $(selector + '-icon').removeClass('fa-plus').addClass('fa-minus');
                        }
                    };

                    $('.jqui-accordion').each(function () {
                        var active = false,
                            list = Store('accordions'),
                            found = false,
                            id, base, i;

                        if ($(this).attr('data-open-first')) {
                            active = 0;
                        }
                        else {
                            if (list) {
                                id = $(this).attr('id');
                                base = ($location.path().replace(/^\//, '').split('/')[0]);
                                for (i = 0; i < list.length && found === false; i++) {
                                    if (list[i].base === base && list[i].id === id) {
                                        found = true;
                                        active = list[i].active;
                                    }
                                }
                            }
                            if (found === false && $(this).attr('data-open') === 'true') {
                                active = 0;
                            }
                        }

                        $(this).accordion({
                            collapsible: true,
                            heightStyle: 'content',
                            active: active,
                            activate: function () {
                                // Maintain in local storage of list of all accordions by page, recording
                                // the active panel for each. If user navigates away and comes back,
                                // we can activate the last panely viewed.
                                $('.jqui-accordion').each(function () {
                                    var active = $(this).accordion('option', 'active'),
                                        id = $(this).attr('id'),
                                        base = ($location.path().replace(/^\//, '').split('/')[0]),
                                        list = Store('accordions'),
                                        found = false,
                                        i;
                                    if (!list) {
                                        list = [];
                                    }
                                    for (i = 0; i < list.length && found === false; i++) {
                                        if (list[i].base === base && list[i].id === id) {
                                            found = true;
                                            list[i].active = active;
                                        }
                                    }
                                    if (found === false) {
                                        list.push({
                                            base: base,
                                            id: id,
                                            active: active
                                        });
                                    }
                                    Store('accordions', list);
                                });
                            }
                        });
                    });
                }
            },

            genID: function () {
                var id = new Date();
                return id.getTime();
            },

            headerField: function (fld, field) {
                var html = '';
                if (field.label) {
                    html += "<label>" + field.label + "</label>\n";
                }
                html += "<input type=\"text\" name=\"" + fld + "\" ";
                html += "ng-model=\"" + fld + "\" ";
                html += (field['class']) ? Attr(field, "class") : "";
                html += " readonly />\n";
                return html;
            },

            clearApiErrors: function () {
                for (var fld in this.form.fields) {
                    if (this.form.fields[fld].sourceModel) {
                        this.scope[this.form.fields[fld].sourceModel + '_' + this.form.fields[fld].sourceField + '_api_error'] = '';
                        $('[name="' + this.form.fields[fld].sourceModel + '_' + this.form.fields[fld].sourceField + '"]').removeClass('ng-invalid');
                    } else if (this.form.fields[fld].realName) {
                        this.scope[this.form.fields[fld].realName + '_api_error'] = '';
                        $('[name="' + this.form.fields[fld].realName + '"]').removeClass('ng-invalid');
                    } else {
                        this.scope[fld + '_api_error'] = '';
                        $('[name="' + fld + '"]').removeClass('ng-invalid');
                    }
                }
                if (!this.scope.$$phase) {
                    this.scope.$digest();
                }
            },

            button: function(params) {
                var tagName = "button";
                var options = params.btn;
                var tagParts =
                    [   tagName,
                        "toolbar-button"
                    ];

                var attrNames = _.keys(options);

                function isSupportedKey(keyName) {
                    if (keyName === 'icon') {
                        //TODO: Let's add a depecrated logger to our logging helper to output the below message
                        //
                        // The form action key "icon" is deprecated in favor of using the name of the field as the icon name or the iconClass option.
                        return false;
                    }

                    return true;
                }

                var attrs = attrNames
                .filter(function(name) {

                    return isSupportedKey(name) &&
                        !_.isEmpty(options[name]);

                }).map(function(name) {
                    return Attr(options, name);
                });

                tagParts =
                    tagParts
                        .concat(attrs)
                        .concat(
                            Attr(params, 'iconName'),
                            Attr(params, 'toolbar')
                        );

                var html = "<" + tagParts.join(" ") + "></" + tagName + ">";

                return html;

            },

            navigationLink: NavigationLink,


            buildHelpCollapse: function (collapse_array) {
                var html = '',
                    params = {}, i;
                for (i = 0; i < collapse_array.length; i++) {
                    params.hdr = collapse_array[i].hdr;
                    params.content = collapse_array[i].content;
                    params.idx = this.accordion_count++;
                    params.show = (collapse_array[i].show) ? collapse_array[i].show : null;
                    params.ngHide = (collapse_array[i].ngHide) ? collapse_array[i].ngHide : null;
                    params.bind = (collapse_array[i].ngBind) ? collapse_array[i].ngBind : null;
                    html += HelpCollapse(params);
                }
                return html;
            },


            buildField: function (fld, field, options, form) {

                var i, fldWidth, offset, html = '',
                    horizontal = (this.form.horizontal) ? true : false;

                function getFieldWidth() {
                    var x;
                    if (form.formFieldSize) {
                        x = form.formFieldSize;
                    } else if (field.xtraWide) {
                        x = "col-lg-10";
                    } else if (field.column) {
                        x = "col-lg-8";
                    } else if (!form.formFieldSize && options.modal) {
                        x = "col-lg-10";
                    } else {
                        x = "col-lg-6";
                    }
                    return x;
                }

                function getLabelWidth() {
                    var x;
                    if (form.formLabelSize) {
                        x = form.formLabelSize;
                    } else if (field.column) {
                        x = "col-lg-4";
                    } else if (!form.formLabelSize && options.modal) {
                        x = "col-lg-2";
                    } else {
                        x = "col-lg-2";
                    }
                    return x;
                }

                function buildId(field, fld, form) {
                    var html = '';
                    if (field.id) {
                        html += Attr(field, 'id');
                    } else {
                        html += "id=\"" + form.name + "_" + fld + "\" ";
                    }
                    return html;
                }

                function buildCheckbox(form, field, fld, idx, includeLabel) {
                    var html = '',
                        label = (includeLabel !== undefined && includeLabel === false) ? false : true;

                    if (label) {
                        html += "<label class=\"";
                        html += (field.inline === undefined || field.inline === true) ? "checkbox-inline" : "";
                        html += (field.labelClass) ? " " + field.labelClass : "";
                        html += "\">";
                    }

                    html += "<input type=\"checkbox\" ";
                    html += Attr(field, 'type');
                    html += "ng-model=\"" + fld + '" ';
                    html += "name=\"" + fld + '" ';
                    html += (field.ngChange) ? Attr(field, 'ngChange') : "";
                    html += "id=\"" + form.name + "_" + fld + "_chbox\" ";
                    html += (idx !== undefined) ? "_" + idx : "";
                    html += "class=\"";
                    html += (field['class']) ? field['class'] + " " : "";
                    html += "\"";
                    html += (field.trueValue !== undefined) ? Attr(field, 'trueValue') : "";
                    html += (field.falseValue !== undefined) ? Attr(field, 'falseValue') : "";
                    html += (field.checked) ? "checked " : "";
                    html += (field.readonly) ? "disabled " : "";
                    html += (field.ngChange) ? "ng-change=\"" +field.ngChange + "\" " : "";
                    html += (field.ngDisabled) ? "ng-disabled=\"" + field.ngDisabled + "\" " : "";
                    html += " > ";

                    if (label) {
                        html += field.label + " ";
                        html += (field.awPopOver) ? Attr(field, 'awPopOver', fld) : "";
                        html += "</label>\n";
                    }

                    return html;
                }

                function label() {
                    var html = '';
                    if (field.label || field.labelBind) {
                        html += "<label ";
                        if (horizontal || field.labelClass) {
                            html += "class=\"";
                            html += (field.labelClass) ? field.labelClass : "";
                            html += (horizontal) ? " " + getLabelWidth() : "";
                            html += "\" ";
                        }
                        html += (field.labelNGClass) ? "ng-class=\"" + field.labelNGClass + "\" " : "";
                        html += "for=\"" + fld + '">\n';
                        html += (field.icon) ? Icon(field.icon) : "";
                        if (field.labelBind) {
                            html += "\t\t<span class=\"label-text\" ng-bind=\"" + field.labelBind + "\">\n\t\t</span>";
                        } else {
                            html += "\t\t<span class=\"label-text\">\n\t\t\t" + field.label + "\n\t\t</span>";
                        }
                        html += (field.awPopOver && !field.awPopOverRight) ? Attr(field, 'awPopOver', fld) : "";
                        html += (field.hintText) ? "\n\t\t<span class=\"label-hint-text\">\n\t\t\t<i class=\"fa fa-info-circle\">\n\t\t\t</i>\n\t\t\tHint: " + field.hintText + "\n\t\t</span>" : "";
                        html += "\n\t</label>\n";
                    }
                    return html;
                }


                if (field.type === 'alertblock') {
                    html += "<div class=\"row\">\n";
                    html += "<div class=\"";
                    html += (options.modal || options.id) ? "col-lg-12" : "col-lg-8 col-lg-offset-2";
                    html += "\">\n";
                    html += "<div class=\"alert";
                    html += (field.closeable === undefined || field.closeable === true) ? " alert-dismissable" : "";
                    html += (field['class']) ? " " + field['class'] : "";
                    html += "\" ";
                    html += (field.ngShow) ? this.attr(field, 'ngShow') : "";
                    html += ">\n";
                    html += (field.closeable === undefined || field.closeable === true) ?
                        "<button type=\"button\" class=\"close\" data-dismiss=\"alert\" aria-hidden=\"true\">&times;</button>\n" : "";
                    html += field.alertTxt;
                    html += "</div>\n";
                    html += "</div>\n";
                    html += "</div>\n";
                }

                if (field.type === 'hidden') {
                    if ((options.mode === 'edit' && field.includeOnEdit) ||
                        (options.mode === 'add' && field.includeOnAdd)) {
                        html += "<input type=\"hidden\" ng-model=\"" + fld + "\" name=\"" + fld + "\" />";
                    }
                }

                if ((!field.readonly) || (field.readonly && options.mode === 'edit')) {
                    html += "<div class='form-group ";
                    html += (field['class']) ? (field['class']) : "";
                    html += "'";
                    html += (field.ngShow) ? this.attr(field, 'ngShow') : "";
                    html += (field.ngHide) ? this.attr(field, 'ngHide') : "";
                    html += (field.awFeature) ? "aw-feature=\"" + field.awFeature + "\" " : "";
                    html += ">\n";

                    //text fields
                    if (field.type === 'text' || field.type === 'password' || field.type === 'email') {
                        html += label();
                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";

                        html += (field.clear || field.genMD5) ? "<div class=\"input-group\">\n" : "";

                        if (field.control === null || field.control === undefined || field.control) {
                            html += "<input ";
                            html += this.attr(field, 'type');
                            html += "ng-model=\"" + fld + '" ';
                            html += 'name="' + fld + '" ';
                            html += (field.ngChange) ? this.attr(field, 'ngChange') : "";
                            html += buildId(field, fld, this.form);
                            html += (field.controlNGClass) ? "ng-class=\"" + field.controlNGClass + "\" " : "";
                            html += "class=\"form-control";
                            html += (field['class']) ? " " + this.attr(field, 'class') : "";
                            html += "\" ";
                            html += (field.placeholder) ? this.attr(field, 'placeholder') : "";
                            html += (options.mode === 'edit' && field.editRequired) ? "required " : "";
                            html += (options.mode === 'add' && field.addRequired) ? "required " : "";
                            html += (field.readonly || field.showonly) ? "readonly " : "";
                            html += (field.awPassMatch) ? "awpassmatch=\"" + field.associated + "\" " : "";
                            html += (field.capitalize) ? "capitalize " : "";
                            html += (field.awSurveyQuestion) ? "aw-survey-question" : "" ;
                            html += (field.ask) ? "ng-disabled=\"" + fld + "_ask\" " : "";
                            html += (field.autocomplete !== undefined) ? this.attr(field, 'autocomplete') : "";
                            html += (field.awRequiredWhen) ? "data-awrequired-init=\"" + field.awRequiredWhen.init + "\" aw-required-when=\"" +
                                field.awRequiredWhen.variable + "\" " : "";
                            html += (field.awValidUrl) ? "aw-valid-url " : "";
                            html += (field.associated && this.form.fields[field.associated].ask) ? "ng-disabled=\"" + field.associated + "_ask\" " : "";
                            html += ">\n";
                        }

                        if (field.clear) {
                            html += "<span class=\"input-group-btn\"><button type=\"button\" ";
                            html += "id=\"" + this.form.name + "_" + fld + "_clear_btn\" ";
                            html += "class=\"btn btn-default\" ng-click=\"clear('" + fld + "','" + field.associated + "')\" " +
                                "aw-tool-tip=\"Clear " + field.label + "\" id=\"" + fld + "-clear-btn\" ";
                            html += (field.ask) ? "ng-disabled=\"" + fld + "_ask\" " : "";
                            html += " ><i class=\"fa fa-undo\"></i></button>\n";
                            html += "</span>\n</div>\n";
                            if (field.ask) {
                                html += "<label class=\"checkbox-inline ask-checkbox\" ";
                                html += (field.askShow) ? "ng-show=\"" + field.askShow + "\" " : "";
                                html += ">";
                                html += "<input type=\"checkbox\" ng-model=\"" +
                                    fld + "_ask\" ng-change=\"ask('" + fld + "','" + field.associated + "')\" ";
                                html += "id=\"" + this.form.name + "_" + fld + "_ask_chbox\" ";
                                html += "> Ask at runtime?</label>";
                            }
                        }

                        if (field.genMD5) {
                            html += "<span class=\"input-group-btn\"><button type=\"button\" class=\"btn btn-default\" ng-click=\"genMD5('" + fld + "')\" " +
                                "aw-tool-tip=\"Generate " + field.label + "\" data-placement=\"top\" id=\"" + this.form.name + "_" + fld + "_gen_btn\">" +
                                "<i class=\"fa fa-magic\"></i></button></span>\n</div>\n";
                        }

                        // Add error messages
                        if ((options.mode === 'add' && field.addRequired) || (options.mode === 'edit' && field.editRequired) ||
                            field.awRequiredWhen) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-required-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.required\">Please enter a value.</div>\n";
                        }
                        if (field.type === "email") {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-email-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.email\">Please enter a valid email address.</div>\n";
                        }
                        if (field.awPassMatch) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-passmatch-error\" ng-show=\"" + this.form.name + '_form.' + fld +
                                ".$error.awpassmatch\">This value does not match the password you entered previously.  Please confirm that password.</div>\n";
                        }
                        if (field.awValidUrl) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-url-error\" ng-show=\"" + this.form.name + '_form.' + fld +
                                ".$error.awvalidurl\">Please enter a URL that begins with ssh, http or https.  The URL may not contain the '@' character. </div>\n";
                        }

                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";

                        // Add help panel(s)
                        html += (field.helpCollapse) ? this.buildHelpCollapse(field.helpCollapse) : '';

                        html += "</div>\n";
                    }

                    //fields with sensitive data that needs to be obfuscated from view
                    if (field.type === 'sensitive') {
                        field.showInputInnerHTML = "ABC";
                        field.inputType = "password";

                        html += "\t" + label();
                        if (field.hasShowInputButton) {
                            field.toggleInput = function(id) {
                                var buttonId = id + "_show_input_button",
                                    inputId = id + "_input",
                                    buttonInnerHTML = $(buttonId).html();
                                if (buttonInnerHTML.indexOf("ABC") > -1) {
                                    $(buttonId).html("<i class=\"fa fa-asterisk\"></i><i class=\"fa fa-asterisk\"></i><i class=\"fa fa-asterisk\"></i>");
                                    $(inputId).attr("type", "text");
                                } else {
                                    $(buttonId).html("ABC");
                                    $(inputId).attr("type", "password");
                                }
                            };
                            html += "\<div class='input-group";
                            html += (horizontal) ? " " + getFieldWidth() : "";
                            html += "'>\n";
                            // TODO: make it so that the button won't show up if the mode is edit, hasShowInputButton !== true, and there are no contents in the field.
                            html += "<span class='input-group-btn'>\n";
                            html += "<button class='btn btn-default' ";
                            html += buildId(field, fld + "_show_input_button", this.form);
                            html += "aw-tool-tip='Toggle the display of plaintext.' aw-tip-placement='top' ";
                            html += "ng-click='" + fld + "_field.toggleInput(\"#" + this.form.name + "_" + fld + "\")'";
                            html += (field.ask) ? " ng-disabled='" + fld + "_ask'" : "";
                            html += ">\n" + field.showInputInnerHTML;
                            html += "\n</button>\n";
                            html += "</span>\n";
                        } else {
                            html += "<div";
                            html += (horizontal) ? " class='" + getFieldWidth() + "'" : "";
                            html += ">\n";
                        }

                        if (field.control === null || field.control === undefined || field.control) {
                            html += "<input ";
                            html += buildId(field, fld + "_input", this.form);
                            html += "type='password' ";
                            html += "ng-model=\"" + fld + '" ';
                            html += 'name="' + fld + '" ';

                            html += (field.ngChange) ? this.attr(field, 'ngChange') : "";
                            html += buildId(field, fld, this.form);

                            html += (field.controlNGClass) ? "ng-class='" + field.controlNGClass + "' " : "";
                            html += "class='form-control";
                            html += (field['class']) ? " " + this.attr(field, 'class') : "";
                            html += "' ";
                            html += (field.chkPass) ? "chk-pass " : "";

                            html += (field.placeholder) ? this.attr(field, 'placeholder') : "";
                            html += (options.mode === 'edit' && field.editRequired) ? "required " : "";
                            html += (options.mode === 'add' && field.addRequired) ? "required " : "";

                            html += (field.readonly || field.showonly) ? "readonly " : "";

                            html += (field.awPassMatch) ? "awpassmatch='" + field.associated + "' " : "";
                            html += (field.capitalize) ? "capitalize " : "";
                            html += (field.awSurveyQuestion) ? "aw-survey-question" : "";
                            html += (field.ask) ? "ng-disabled='" + fld + "_ask' " : "";
                            html += (field.autocomplete !== undefined) ? this.attr(field, 'autocomplete') : "";
                            html += (field.awRequiredWhen) ? "data-awrequired-init='" + field.awRequiredWhen.init + "' aw-required-when='" +
                                field.awRequiredWhen.variable + "' " : "";
                            html += (field.awValidUrl) ? "aw-valid-url " : "";
                            html += (field.associated && this.form.fields[field.associated].ask) ? "ng-disabled='" + field.associated + "_ask' " : "";
                            html += ">\n";
                        }

                        html += "</div>\n";

                        // if (field.clear) {
                        //     html += "<span class=\"input-group-btn\"><button type=\"button\" ";
                        //     html += "id=\"" + this.form.name + "_" + fld + "_clear_btn\" ";
                        //     html += "class=\"btn btn-default\" ng-click=\"clear('" + fld + "','" + field.associated + "')\" " +
                        //         "aw-tool-tip=\"Clear " + field.label + "\" id=\"" + fld + "-clear-btn\" ";
                        //     html += (field.ask) ? "ng-disabled=\"" + fld + "_ask\" " : "";
                        //     html += " ><i class=\"fa fa-undo\"></i></button>\n";
                        //     html += "</span>\n</div>\n";
                        //
                        // }

                        if (field.ask) {
                            html += "<label class=\"checkbox-inline ask-checkbox\" ";
                            html += (field.askShow) ? "ng-show=\"" + field.askShow + "\" " : "";
                            html += ">";
                            html += "<input type=\"checkbox\" ng-model=\"" +
                                fld + "_ask\" ng-change=\"ask('" + fld + "','" + field.associated + "')\" ";
                            html += "id=\"" + this.form.name + "_" + fld + "_ask_chbox\" ";
                            html += "> Ask at runtime?</label>";
                        }

                        // if (field.genMD5) {
                        //     html += "<span class=\"input-group-btn\"><button type=\"button\" class=\"btn btn-default\" ng-click=\"genMD5('" + fld + "')\" " +
                        //         "aw-tool-tip=\"Generate " + field.label + "\" data-placement=\"top\" id=\"" + this.form.name + "_" + fld + "_gen_btn\">" +
                        //         "<i class=\"fa fa-magic\"></i></button></span>\n</div>\n";
                        // }

                        // Add error messages
                        if ((options.mode === 'add' && field.addRequired) || (options.mode === 'edit' && field.editRequired) ||
                            field.awRequiredWhen) {
                            html += "<div class='error' id='" + this.form.name + "-" + fld + "-required-error' ng-show='" + this.form.name + "_form." + fld + ".$dirty && " +
                                this.form.name + "_form." + fld + ".$error.required'>\nPlease enter a value.\n</div>\n";
                        }
                        if (field.type === "email") {
                            html += "<div class='error' id='" + this.form.name + "-" + fld + "-email-error' ng-show='" + this.form.name + "_form." + fld + ".$dirty && " +
                                this.form.name + "_form." + fld + ".$error.email'>\nPlease enter a valid email address.\n</div>\n";
                        }
                        if (field.awPassMatch) {
                            html += "<div class='error' id='" + this.form.name + "-" + fld + "-passmatch-error' ng-show='" + this.form.name + "_form." + fld +
                                ".$error.awpassmatch'>\nThis value does not match the password you entered previously.  Please confirm that password.\n</div>\n";
                        }
                        if (field.awValidUrl) {
                            html += "<div class='error' id='" + this.form.name + "-" + fld + "-url-error' ng-show='" + this.form.name + "_form." + fld +
                                ".$error.awvalidurl'>\nPlease enter a URL that begins with ssh, http or https.  The URL may not contain the '@' character.\n</div>\n";
                        }
                        if (field.chkPass) {
                            // password strength
                            if ($AnsibleConfig.password_length) {
                                html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld +
                                    ".$error.password_length\">Your password must be " + $AnsibleConfig.password_length + " characters long.</div>\n";
                            }
                            if ($AnsibleConfig.password_hasLowercase) {
                                html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld +
                                    ".$error.hasLowercase\">Your password must contain a lowercase letter.</div>\n";
                            }
                            if ($AnsibleConfig.password_hasUppercase) {
                                html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld +
                                    ".$error.hasUppercase\">Your password must contain an uppercase letter.</div>\n";
                            }
                            if ($AnsibleConfig.password_hasNumber) {
                                html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld +
                                    ".$error.hasNumber\">Your password must contain a number.</div>\n";
                            }
                            if ($AnsibleConfig.password_hasSymbol) {
                                html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld +
                                    ".$error.hasSymbol\">Your password must contain one of the following characters: -!$%^&*()_+|~=`{}\[\]:\";\'<>?,.\/.</div>\n";
                            }
                        }

                        html += "<div class='error api-error' id='" + this.form.name + "-" + fld + "-api-error' ng-bind='" + fld + "_api_error'>\n</div>\n";

                        // Add help panel(s)
                        html += (field.helpCollapse) ? this.buildHelpCollapse(field.helpCollapse) : '';
                    }

                    //textarea fields
                    if (field.type === 'textarea') {

                        html += label();

                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";

                        // Variable editing
                        if (fld === "variables" || fld === "extra_vars" || fld === 'inventory_variables' || fld === 'source_vars') {
                            html += "<div class=\"parse-selection\" id=\"" + this.form.name + "_" + fld + "_parse_type\">Parse as: " +
                                "<input type=\"radio\" ng-disabled=\"disableParseSelection\" ng-model=\"";
                            html += (field.parseTypeName) ? field.parseTypeName : 'parseType';
                            html += "\" value=\"yaml\" ng-change=\"parseTypeChange()\"> <span class=\"parse-label\">YAML</span>\n";
                            html += "<input type=\"radio\" ng-disabled=\"disableParseSelection\" ng-model=\"";
                            html += (field.parseTypeName) ? field.parseTypeName : 'parseType';
                            html += "\" value=\"json\" ng-change=\"parseTypeChange()\"> <span class=\"parse-label\">JSON</span>\n";
                            html += "</div>\n";
                        }

                        html += "<textarea ";
                        html += (field.rows) ? this.attr(field, 'rows') : "";
                        html += "ng-model=\"" + fld + '" ';
                        html += 'name="' + fld + '" ';
                        html += "class=\"form-control";
                        html += (field['class']) ? " " + field['class'] : "";
                        html += "\" ";
                        html += (field.ngChange) ? this.attr(field, 'ngChange') : "";
                        html += buildId(field, fld, this.form);
                        html += (field.placeholder) ? this.attr(field, 'placeholder') : "";
                        html += (options.mode === 'edit' && field.editRequired) ? "required " : "";
                        html += (options.mode === 'add' && field.addRequired) ? "required " : "";
                        html += (field.ngRequired) ? "ng-required=\"" + field.ngRequired +"\"" : "";
                        html += (field.readonly || field.showonly) ? "readonly " : "";
                        html += (field.awDropFile) ? "aw-drop-file " : "";
                        html += (field.awRequiredWhen) ? "data-awrequired-init=\"" + field.awRequiredWhen.init + "\" aw-required-when=\"" +
                            field.awRequiredWhen.variable + "\" " : "";
                        html += "aw-watch ></textarea>\n";


                        // Add error messages
                        if ((options.mode === 'add' && field.addRequired) || (options.mode === 'edit' && field.editRequired)) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-required-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.required\">Please enter a value.</div>\n";
                        }
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
                        html += "</div>\n";
                    }

                    //select field
                    if (field.type === 'select') {

                        html += label();

                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";

                        html += "<select ";
                        html += "ng-model=\"" + fld + '" ';
                        html += 'name="' + fld + '" ';
                        html += "class=\"form-control";
                        html += (field['class']) ? " " + field['class'] : "";
                        html += "\" ";
                        html += (field.ngOptions) ? this.attr(field, 'ngOptions') : "" ;
                        html += (field.ngChange) ? this.attr(field, 'ngChange') : "";
                        html += (field.ngDisabled) ? this.attr(field, 'ngDisabled'): "";
                        html += (field.ngRequired) ? this.attr(field, 'ngRequired') : "";
                        html += buildId(field, fld, this.form);
                        html += (options.mode === 'edit' && field.editRequired) ? "required " : "";
                        html += (options.mode === 'add' && field.addRequired) ? "required " : "";
                        html += (field.multiSelect) ? "multiple " : "";
                        html += (field.readonly) ? "disabled " : "";
                        html += (field.awRequiredWhen) ? "data-awrequired-init=\"" + field.awRequiredWhen.init + "\" aw-required-when=\"" +
                            field.awRequiredWhen.variable + "\" " : "";
                        html += ">\n";
                        html += "<option value=\"\">";
                            // Add a custom default select 'value' (default text)
                        html += (field.defaultText) ? field.defaultText : "Choose a " + field.label.toLowerCase();
                        html += "</option>\n";
                        html += "</select>\n";
                            // Add error messages
                        if ((options.mode === 'add' && field.addRequired) || (options.mode === 'edit' && field.editRequired) ||
                            field.awRequiredWhen) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-required-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.required\">Please select a value.</div>\n";
                        }
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";

                        // Add help panel(s)
                        html += (field.helpCollapse) ? this.buildHelpCollapse(field.helpCollapse) : '';

                        html += "</div>\n";
                    }

                    //number field
                    if (field.type === 'number') {

                        html += label();

                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";

                        html += "<input ";
                        html += (field.spinner) ? "" : "type=\"text\" ";
                        html += "\" value=\"" + field['default'] + "\" ";
                        html += "class=\"";
                        if (!field.slider && !field.spinner) {
                            html += "form-control";
                        }
                        html += (field['class']) ? " " + field['class'] : "";
                        html += "\" ";
                        html += (field.slider) ? "aw-slider=\"" + fld + "\" " : "";
                        html += (field.spinner) ? "aw-spinner=\"" + fld + "\" " : "";
                        html += "ng-model=\"" + fld + '" ';
                        html += 'name="' + fld + '" ';
                        html += buildId(field, fld, this.form);
                        html += (field.min || field.min === 0) ? this.attr(field, 'min') : "";
                        html += (field.max) ? this.attr(field, 'max') : "";
                        html += (field.ngChange) ? this.attr(field, 'ngChange') : "";
                        html += (field.slider) ? "id=\"" + fld + "-number\"" : (field.id) ? this.attr(field, 'id') : "";
                        html += (options.mode === 'edit' && field.editRequired) ? "required " : "";
                        html += (options.mode === 'add' && field.addRequired) ? "required " : "";
                        html += (field.readonly) ? "readonly " : "";
                        html += (field.integer) ? "integer " : "";
                        html += (field.disabled) ? "data-disabled=\"true\" " : "";
                        html += " >\n";
                        // Add error messages
                        if ((options.mode === 'add' && field.addRequired) || (options.mode === 'edit' && field.editRequired)) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-required-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.required\">Please enter a value.</div>\n";
                        }
                        if (field.integer) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-integer-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.integer\">Please enter a number.</div>\n";
                        }
                        if (field.min !== undefined || field.max !== undefined) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-minmax-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.min || " +
                                this.form.name + '_form.' + fld + ".$error.max\">Please enter a number greater than " + field.min;
                            html += (field.max !== undefined) ? " and less than " + field.max + "." : ".";
                            html += "</div>\n";
                        }
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
                        html += "</div>\n";
                    }

                    //checkbox group
                    if (field.type === 'checkbox_group') {

                        html += label();

                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";

                        html += "<div class=\"checkbox-group\" ";
                        html += "id=\"" + this.form.name + "_" + fld + "_chbox_group\" ";
                        html += ">\n";
                        for (i = 0; i < field.fields.length; i++) {
                            html += buildCheckbox(this.form, field.fields[i], field.fields[i].name, i);
                        }
                        // Add error messages
                        if ((options.mode === 'add' && field.addRequired) || (options.mode === 'edit' && field.editRequired)) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-required-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.required\">Please select at least one value.</div>\n";
                        }
                        if (field.integer) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-integer-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.integer\">Please select a number.</div>\n";
                        }
                        if (field.min || field.max) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-minmax-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.min || " +
                                this.form.name + '_form.' + fld + ".$error.max\">Please select a number between " + field.min + " and " +
                                field.max + "</div>\n";
                        }
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
                        html += "</div><!-- checkbox-group -->\n";
                        html += "</div>\n";
                    }

                    //checkbox
                    if (field.type === 'checkbox') {

                        if (horizontal) {
                            fldWidth = getFieldWidth();
                            offset = 12 - parseInt(fldWidth.replace(/[A-Z,a-z,-]/g, ''),10);
                            html += "<div class=\"" + fldWidth + " col-lg-offset-" + offset + "\">\n";
                        }

                        html += "<div class=\"checkbox\">\n";
                        html += "<label ";
                        html += (field.labelBind) ? "ng-bind=\"" + field.labelBind + "\" " : "";
                        //html += "for=\"" + fld + '">';
                        html += ">";
                        html += buildCheckbox(this.form, field, fld, undefined, false);
                        html += (field.icon) ? Icon(field.icon) : "";
                        html += '<span class=\"label-text\">' + field.label + "</span>";
                        html += (field.awPopOver) ? this.attr(field, 'awPopOver', fld) : "";
                        html += "</label>\n";
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" +
                            fld + "_api_error\"></div>\n";
                        html += "</div><!-- checkbox -->\n";

                        if (horizontal) {
                            html += "</div>\n";
                        }

                        html += (field.helpCollapse) ? this.buildHelpCollapse(field.helpCollapse) : '';
                    }

                    //radio group
                    if (field.type === 'radio_group') {

                        html += label();

                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";

                        for (i = 0; i < field.options.length; i++) {
                            html += "<label class=\"radio-inline\" ";
                            html += (field.options[i].ngShow) ? this.attr(field.options[i], 'ngShow') : "";
                            html += ">";
                            html += "<input type=\"radio\" ";
                            html += "name=\"" + fld + "\" ";
                            html += "value=\"" + field.options[i].value + "\" ";
                            html += "ng-model=\"" + fld + "\" ";
                            html += (field.ngChange) ? this.attr(field, 'ngChange') : "";
                            html += (field.readonly) ? "disabled " : "";
                            html += (options.mode === 'edit' && field.editRequired) ? "required " : "";
                            html += (options.mode === 'add' && field.addRequired) ? "required " : "";
                            html += (field.ngDisabled) ? this.attr(field, 'ngDisabled') : "";
                            html += " > " + field.options[i].label + "\n";
                            html += "</label>\n";
                        }
                        if ((options.mode === 'add' && field.addRequired) || (options.mode === 'edit' && field.editRequired)) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-required-error\" ng-show=\"" +
                                this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.required\">Please select a value.</div>\n";
                        }
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" +
                            fld + "_api_error\"></div>\n";

                        // Add help panel(s)
                        html += (field.helpCollapse) ? this.buildHelpCollapse(field.helpCollapse) : '';

                        html += "</div>\n";
                    }

                    // radio button
                    if (field.type === 'radio') {

                        if (horizontal) {
                            fldWidth = getFieldWidth();
                            offset = 12 - parseInt(fldWidth.replace(/[A-Z,a-z,-]/g, ''),10);
                            html += "<div class=\"" + fldWidth + " col-lg-offset-" + offset + "\">\n";
                        }

                        html += "<div class=\"radio\">\n";
                        html += "<label ";
                        html += (field.labelBind) ? "ng-bind=\"" + field.labelBind + "\" " : "";
                        html += "for=\"" + fld + '">';

                        html += "<input type=\"radio\" ";
                        html += "name=\"" + fld + "\" ";
                        html += "value=\"" + field.value + "\" ";
                        html += "ng-model=\"" + field.ngModel + "\" ";
                        html += (field.ngChange) ? Attr(field, 'ngChange') : "";
                        html += (field.readonly) ? "disabled " : "";
                        html += (field.ngDisabled) ? Attr(field, 'ngDisabled') : "";
                        html += " > ";
                        html += field.label;
                        html += "</label>\n";
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" +
                            fld + "_api_error\"></div>\n";
                        html += "</div><!-- radio -->\n";

                        if (horizontal) {
                            html += "</div>\n";
                        }
                    }

                    //lookup type fields
                    if (field.type === 'lookup' && (field.excludeMode === undefined || field.excludeMode !== options.mode)) {

                        html += label();

                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";

                        html += "<div class=\"input-group\">\n";
                        html += "<span class=\"input-group-btn\">\n";
                        html += "<button type=\"button\" class=\"lookup-btn btn btn-default\" " + this.attr(field, 'ngClick');
                        html += (field.readonly || field.showonly) ? " disabled " : "";
                        html += (field.ngDisabled) ? this.attr(field, "ngDisabled"): "";
                        html += "id=\"" + fld + "-lookup-btn\"><i class=\"fa fa-search\"></i></button>\n";
                        html += "</span>\n";
                        html += "<input type=\"text\" class=\"form-control input-medium lookup\" ";
                        html += "ng-model=\"" + field.sourceModel + '_' + field.sourceField + "\" ";
                        html += "name=\"" + field.sourceModel + '_' + field.sourceField + "\" ";
                        html += "class=\"form-control\" ";
                        html += (field.ngChange) ? this.attr(field, 'ngChange') : "";
                        html += (field.ngDisabled) ? this.attr(field, 'ngDisabled') : "" ;
                        html += (field.ngRequired) ? this.attr(field, 'ngRequired') : "";
                        html += (field.id) ? this.attr(field, 'id') : "";
                        html += (field.placeholder) ? this.attr(field, 'placeholder') : "";
                        html += (options.mode === 'edit' && field.editRequired) ? "required " : "";
                        html += (field.readonly || field.showonly) ? "readonly " : "";
                        html += (field.awRequiredWhen) ? "data-awrequired-init=\"" + field.awRequiredWhen.init + "\" aw-required-when=\"" +
                            field.awRequiredWhen.variable + "\" " : "";
                        html += " awlookup >\n";
                        html += "</div>\n";
                        // Add error messages
                        if ((options.mode === 'add' && field.addRequired) || (options.mode === 'edit' && field.editRequired) ||
                            field.awRequiredWhen) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-required-error\" ng-show=\"" +
                                this.form.name + '_form.' +
                                field.sourceModel + '_' + field.sourceField + ".$dirty && " +
                                this.form.name + '_form.' + field.sourceModel + '_' + field.sourceField +
                                ".$error.required\">Please select a value.</div>\n";
                        }
                        html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-notfound-error\" ng-show=\"" +
                            this.form.name + '_form.' +
                            field.sourceModel + '_' + field.sourceField + ".$dirty && " +
                            this.form.name + '_form.' + field.sourceModel + '_' + field.sourceField +
                            ".$error.awlookup\">That value was not found.  Please enter or select a valid value.</div>\n";
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" + field.sourceModel + '_' + field.sourceField +
                            "_api_error\"></div>\n";
                        html += "</div>\n";
                    }

                    //custom fields
                    if (field.type === 'custom') {
                        html += label();
                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";
                        html += "<div ";
                        html += "id=\"" + form.name + "_" + fld + "\" ";
                        html += (field.controlNGClass) ? "ng-class=\"" + field.controlNGClass + "\" " : "";
                        html += ">\n";
                        html += field.control;
                        html += "</div>\n";
                        html += "</div>\n";
                    }
                    html += "</div>\n";
                }
                return html;
            },

            getActions: function (options) {
                // Use to add things like Activity Stream to a detail page
                var html = "<div class=\"list-actions\">\n", action;
                for (action in this.form.actions) {
                    if (this.form.actions[action].mode === 'all' || this.form.actions[action].mode === options.mode) {
                        html += this.button({ btn: this.form.actions[action], iconName: action, toolbar: true });
                    }
                }
                html += "</div>\n";
                return html;
            },


            breadCrumbs: function (options, navigation) {

                var itm, paths, html = '';
                html += "<ul class=\"ansible-breadcrumb\">\n";
                html += "<li ng-repeat=\"crumb in breadcrumbs\"><a href=\"{{ '#' + crumb.path }}\">{{ crumb.title }}</a></li>\n";

                if (navigation) {
                    paths = $location.path().replace(/^\//, '').split('/');
                    if (paths.length === 2) {
                        html += "<li class=\"active\">";
                        if (options.mode === 'edit') {
                            html += this.form.editTitle;
                        } else {
                            html += this.form.addTitle;
                        }
                        html += "</li>\n";
                    }

                    html += "<li class=\"active\"> </li>\n";
                    html += "</ul>\n";
                    html += "<div class=\"dropdown\">\n";
                    for (itm in navigation) {
                        if (navigation[itm].active) {
                            html += "<a href=\"\" class=\"toggle\" ";
                            html += "data-toggle=\"dropdown\" ";
                            html += ">" + navigation[itm].label + " <i class=\"fa fa-chevron-circle-down crumb-icon\"></i></a>";
                            break;
                        }
                    }

                    html += "<ul class=\"dropdown-menu\" role=\"menu\">\n";
                    for (itm in navigation) {
                        html += "<li role=\"presentation\"><a role=\"menuitem\" tabindex=\"-1\" href=\"" +
                            navigation[itm].href + "\" ";
                        // html += (navigation[itm].active) ? "class=\"active\" " : "";
                        html += ">";
                        html += "<i class=\"fa fa-check\" style=\"visibility: ";
                        html += (navigation[itm].active) ? "visible" : "hidden";
                        html += "\"></i> ";
                        html += (navigation[itm].listLabel) ? navigation[itm].listLabel : navigation[itm].label;
                        html += "</a></li>\n";
                    }
                    html += "</ul>\n";
                    html += "</div><!-- dropdown -->\n";
                } else {
                    html += "<li class=\"active\"><a href=\"\">";
                    if (options.mode === 'edit') {
                        html += this.form.editTitle;
                    } else {
                        html += this.form.addTitle;
                    }
                    html += "</a></li>\n</ul> <!-- group-breadcrumbs -->\n";
                }
                return html;
            },

            build: function (options) {
                //
                // Generate HTML. Do NOT call this function directly. Called by inject(). Returns an HTML
                // string to be injected into the current view.
                //
                var btn, button, fld, field, html = '', i, section, group,
                    tab, sectionShow, offset, width,ngDisabled;

                if (!this.modal && (options.breadCrumbs === undefined || options.breadCrumbs === true)) {
                    if (this.form.navigationLinks) {
                        html += this.breadCrumbs(options, this.form.navigationLinks);
                    } else {
                        html += this.breadCrumbs(options);
                    }
                }

                if (this.form.collapse && this.form.collapseMode === options.mode) {
                    html += "<div id=\"" + this.form.name + "-collapse-0\" ";
                    html += (this.form.collapseOpen) ? "data-open=\"true\" " : "";
                    html += (this.form.collapseOpenFirst) ? "data-open-first=\"true\" " : "";
                    html += "class=\"jqui-accordion\">\n";
                    html += "<h3>" + this.form.collapseTitle + "</h3>\n";
                    html += "<div>\n";
                    options.collapseAlreadyStarted = true;
                }

                // Start the well
                if (!this.modal && this.form.well) {
                    if ( !(this.form.collapse && this.form.collapseMode === options.mode)) {
                        html += "<div class=\"aw-form-well\">\n";
                    }
                }

                if ((options.showActions === undefined || options.showActions === true) && !this.modal && this.form.actions) {
                    html += this.getActions(options);
                }

                // Add a title and optionally a close button (used on Inventory->Groups)
                /*if ((!options.modal) && this.form.showTitle) {
                    html += "<div class=\"form-title\">";
                    html += (options.mode === 'edit') ? this.form.editTitle : this.form.addTitle;
                    if (this.has('titleActions')) {
                        html += "<div class=\"title-actions pull-right\">\n";
                        for (btn in this.form.titleActions) {
                            html += this.button({
                                btn: this.form.titleActions[btn],
                                action: btn,
                                toolbar: true
                            });
                        }
                        html += "</div>\n";
                    }
                    html += "</div>\n";
                    html += "<hr class=\"form-title-hr\">\n";
                }*/

                html += "<form class=\"";
                html += (this.form.horizontal) ? "form-horizontal" : "";
                html += (this.form['class']) ? ' ' + this.form['class'] : '';
                html += "\" name=\"" + this.form.name + "_form\" id=\"" + this.form.name + "_form\" autocomplete=\"off\" novalidate>\n";
                html += "<div ng-show=\"flashMessage != null && flashMessage != undefined\" class=\"alert alert-info\">{{ flashMessage }}</div>\n";

                if (this.form.twoColumns) {
                    html += "<div class=\"row\">\n";
                    html += "<div class=\"col-lg-6\">\n";
                    for (fld in this.form.fields) {
                        field = this.form.fields[fld];
                        if (field.column === 1) {
                            html += this.buildField(fld, field, options, this.form);
                        }
                    }
                    html += "</div><!-- column 1 -->\n";
                    html += "<div class=\"col-lg-6\">\n";
                    for (fld in this.form.fields) {
                        field = this.form.fields[fld];
                        if (field.column === 2) {
                            html += this.buildField(fld, field, options, this.form);
                        }
                    }
                    html += "</div><!-- column 2 -->\n";
                    html += "</div>\n";
                } else if (this.form.tabs) {
                    html += "<ul id=\"" + this.form.name + "_tabs\" class=\"nav nav-tabs\">\n";
                    for (i = 0; i < this.form.tabs.length; i++) {
                        tab = this.form.tabs[i];
                        html += "<li";
                        if (i === 0) {
                            html += " class=\"active\"";
                        }
                        html += "><a id=\"" + tab.name + "_link\" ng-click=\"toggleTab($event, '" + tab.name + "_link', '" +
                            this.form.name + "_tabs')\" href=\"#" + tab.name + "\" data-toggle=\"tab\">" + tab.label + "</a></li>\n";
                    }
                    html += "</ul>\n";
                    html += "<div class=\"tab-content\">\n";
                    for (i = 0; i < this.form.tabs.length; i++) {
                        tab = this.form.tabs[i];
                        html += "<div class=\"tab-pane";
                        if (i === 0) {
                            html += " active";
                        }
                        html += "\" id=\"" + tab.name + "\">\n";
                        for (fld in this.form.fields) {
                            if (this.form.fields[fld].tab === tab.name) {
                                html += this.buildField(fld, this.form.fields[fld], options, this.form);
                            }
                        }
                        html += "</div>\n";
                    }
                    html += "</div>\n";
                } else {
                    // original, single-column form
                    section = '';
                    group = '';
                    for (fld in this.form.fields) {
                        field = this.form.fields[fld];
                        if (!(options.modal && field.excludeModal)) {
                            if (field.group && field.group !== group) {
                                if (group !== '') {
                                    html += "</div>\n";
                                }
                                html += "<div class=\"well\">\n";
                                html += "<h5>" + field.group + "</h5>\n";
                                group = field.group;
                            }
                            if (field.section && field.section !== section) {
                                if (section !== '') {
                                    html += "</div>\n";
                                } else {
                                    html += "</div>\n";
                                    html += "<div id=\"" + this.form.name + "-collapse\" class=\"jqui-accordion-modal\">\n";
                                }
                                sectionShow = (this.form[field.section + 'Show']) ? " ng-show=\"" + this.form[field.section + 'Show'] + "\"" : "";
                                html += "<h3" + sectionShow + ">" + field.section + "</h3>\n";
                                html += "<div" + sectionShow + ">\n";
                                section = field.section;
                            }
                            html += this.buildField(fld, field, options, this.form);
                        }
                    }
                    if (section !== '') {
                        html += "</div>\n</div>\n";
                    }
                    if (group !== '') {
                        html += "</div>\n";
                    }
                }

                //buttons
                if ((options.showButtons === undefined || options.showButtons === true) && !this.modal) {
                    if (this.has('buttons')) {

                        if (this.form.twoColumns) {
                            html += "<div class=\"row\">\n";
                            html += "<div class=\"col-lg-12\">\n";
                            html += "<hr />\n";
                        }

                        html += "<div class=\"buttons\" ";
                        html += "id=\"" + this.form.name + "_controls\" ";

                        html += ">\n";

                        if (this.form.horizontal) {
                            offset = 2;
                            if (this.form.buttons.labelClass) {
                                offset = parseInt(this.form.buttons.labelClass.replace(/[A-Z,a-z,-]/g, ''));
                            }
                            width = 12 - offset;
                            html += "<div class=\"col-lg-offset-" + offset + " col-lg-" + width + ">\n";
                        }

                        for (btn in this.form.buttons) {
                            if (typeof this.form.buttons[btn] === 'object') {
                                button = this.form.buttons[btn];

                                // Set default color and label for Save and Reset
                                if (btn === 'save') {
                                    button.label = 'Save';
                                    button['class'] = 'btn-primary';
                                }
                                if (btn === 'reset') {
                                    button.label = 'Reset';
                                    button['class'] = 'btn-default';
                                }
                                if (btn === 'launch') {
                                    button.label = 'Launch';
                                    button['class'] = 'btn-primary';
                                }

                                // Build button HTML
                                html += "<button type=\"button\" ";
                                html += "class=\"btn btn-sm";
                                html += (button['class']) ? " " + button['class'] : "";
                                html += "\" ";
                                html += "id=\"" + this.form.name + "_" + btn + "_btn\" ";

                                if(button.ngShow){
                                    html += this.attr(button, 'ngShow');
                                }
                                if (button.ngClick) {
                                    html += this.attr(button, 'ngClick');
                                }
                                if (button.ngDisabled) {
                                    ngDisabled = (button.ngDisabled===true) ? this.form.name+"_form.$invalid" : button.ngDisabled;
                                    if (btn !== 'reset') {
                                        //html += "ng-disabled=\"" + this.form.name + "_form.$pristine || " + this.form.name + "_form.$invalid";
                                        html += "ng-disabled=\"" + ngDisabled;
                                        //html += (this.form.allowReadonly) ? " || " + this.form.name + "ReadOnly == true" : "";
                                        html += "\" ";
                                    } else {
                                        //html += "ng-disabled=\"" + this.form.name + "_form.$pristine";
                                        //html += (this.form.allowReadonly) ? " || " + this.form.name + "ReadOnly == true" : "";
                                        //html += "\" ";
                                    }
                                }
                                html += ">";
                                html += SelectIcon({
                                    action: btn
                                });
                                html += " " + button.label + "</button>\n";
                            }
                        }
                        html += "</div><!-- buttons -->\n";

                        if (this.form.horizontal) {
                            html += "</div>\n";
                        }

                        if (this.form.twoColumns) {
                            html += "</div>\n";
                            html += "</div>\n";
                        }
                    }
                }
                html += "</form>\n";

                if (!this.modal && this.form.well) {
                    if ( !(this.form.collapse && this.form.collapseMode === options.mode)) {
                        html += "</div>\n";
                    }
                }

                if (this.form.collapse && this.form.collapseMode === options.mode) {
                    html += "</div>\n";
                }

                if ((!this.modal) && options.related && this.form.related) {
                    html += this.buildCollections(options);
                }

                return html;
            },

            buildCollections: function (options) {
                //
                // Create TB accordians with imbedded lists for related collections
                // Should not be called directly. Called internally by build().
                //
                var form = this.form,
                    html = '',
                    itm, collection;

                if (!options.collapseAlreadyStarted) {
                    html = "<div id=\"" + this.form.name + "-collapse-1\" class=\"jqui-accordion\">\n";
                }

                for (itm in form.related) {
                    collection = form.related[itm];
                    html += "<h3 class=\"" + itm + "_collapse\">" + (collection.title || collection.editTitle) + "</h3>\n";
                    html += "<div>\n";
                    if (collection.generateList) {
                        html += GenerateList.buildHTML(collection, { mode: 'edit', breadCrumbs: false });
                    }
                    else {
                        html += this.GenerateColleciton({ form: form, related: itm }, options);
                    }
                    html += "</div>\n"; // accordion inner
                }

                if (!options.collapseAlreadyStarted) {
                    html += "</div>\n"; // accordion body
                }

                return html;
            },

            GenerateColleciton: function(params, options) {
                var html = '',
                    form = params.form,
                    itm = params.related,
                    collection = form.related[itm],
                    act, action, fld, cnt, base, fAction;

                if (collection.instructions) {
                    html += "<div class=\"alert alert-info alert-block\">\n";
                    html += "<button type=\"button\" class=\"close\" data-dismiss=\"alert\">&times;</button>\n";
                    html += "<strong>Hint: </strong>" + collection.instructions + "\n";
                    html += "</div>\n";
                }

                //html += "<div class=\"well\">\n";
                html += "<div class=\"row\">\n";

                html += SearchWidget({
                    iterator: collection.iterator,
                    template: collection,
                    mini: true
                });

                html += "<div class=\"col-lg-8\">\n";
                html += "<div class=\"list-actions\">\n";

                for (act in collection.actions) {
                    action = collection.actions[act];
                    html += this.button({
                        btn: action,
                        iconName: act,
                        toolbar: true
                    });
                }

                html += "</div>\n";
                html += "</div>\n";
                html += "</div><!-- row -->\n";

                // Start the list
                html += "<div class=\"list-wrapper\">\n";
                html += "<table id=\"" + itm + "_table" + "\" class=\"" + collection.iterator + " table table-condensed table-hover\">\n";
                html += "<thead>\n";
                html += "<tr>\n";
                html += (collection.index === undefined || collection.index !== false) ? "<th class=\"col-xs-1\">#</th>\n" : "";
                for (fld in collection.fields) {
                    html += "<th class=\"list-header\" id=\"" + collection.iterator + '-' + fld + "-header\" " +
                        "ng-click=\"sort('" + collection.iterator + "', '" + fld + "')\">" +
                        collection.fields[fld].label;
                    html += " <i class=\"";
                    if (collection.fields[fld].key) {
                        if (collection.fields[fld].desc) {
                            html += "fa fa-sort-down";
                        } else {
                            html += "fa fa-sort-up";
                        }
                    } else {
                        html += "fa fa-sort";
                    }
                    html += "\"></i></a></th>\n";
                }
                html += "<th>Actions</th>\n";
                html += "</tr>\n";
                html += "</thead>";
                html += "<tbody>\n";

                html += "<tr ng-repeat=\"" + collection.iterator + " in " + itm + "\" ";
                html += "id=\"{{ " + collection.iterator + ".id }}\">\n";
                if (collection.index === undefined || collection.index !== false) {
                    html += "<td>{{ $index + ((" + collection.iterator + "_page - 1) * " +
                        collection.iterator + "_page_size) + 1 }}.</td>\n";
                }
                cnt = 1;
                base = (collection.base) ? collection.base : itm;
                base = base.replace(/^\//, '');
                for (fld in collection.fields) {
                    cnt++;
                    html += Column({
                        list: collection,
                        fld: fld,
                        options: options,
                        base: base
                    });
                }

                // Row level actions
                html += "<td class=\"actions\">";
                for (act in collection.fieldActions) {
                    fAction = collection.fieldActions[act];
                    html += "<a id=\"" + ((fAction.id) ? fAction.id : act + "-action") + "\" ";
                    html += (fAction.href) ? "href=\"" + fAction.href + "\" " : "";
                    html += (fAction.ngClick) ? this.attr(fAction, 'ngClick') : "";
                    html += (fAction.ngHref) ? this.attr(fAction, 'ngHref') : "";
                    html += (fAction.ngShow) ? this.attr(fAction, 'ngShow') : "";
                    html += ">";
                    html += SelectIcon({ action: act });
                    //html += (fAction.label) ? "<span class=\"list-action-label\"> " + fAction.label + "</span>": "";
                    html += "</a>";
                }
                html += "</td>";
                html += "</tr>\n";

                // Message for when a related collection is empty
                html += "<tr class=\"loading-info\" ng-show=\"" + collection.iterator + "Loading == false && (" + itm + " == null || " + itm + ".length == 0)\">\n";
                html += "<td colspan=\"" + cnt + "\"><div class=\"loading-info\">No records matched your search.</div></td>\n";
                html += "</tr>\n";

                // Message for loading
                html += "<tr ng-show=\"" + collection.iterator + "Loading == true\">\n";
                html += "<td colspan=\"" + cnt + "\"><div class=\"loading-info\">Loading...</div></td>\n";
                html += "</tr>\n";

                // End List
                html += "</tbody>\n";
                html += "</table>\n";
                //html += "</div>\n"; // close well
                html += "</div>\n"; // close list-wrapper div

                html += PaginateWidget({
                    set: itm,
                    iterator: collection.iterator,
                    mini: true
                });
                return html;
            }
        };
    }
]);
