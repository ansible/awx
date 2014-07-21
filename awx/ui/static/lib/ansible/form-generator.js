/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * FormGenerator
 *
 * Pass in a form definition and get back an html template. Use the.inject() method
 * to add the template to the DOM and compile.
 *
 */

'use strict';

angular.module('FormGenerator', ['GeneratorHelpers', 'Utilities', 'ListGenerator'])

.factory('GenerateForm', ['$rootScope', '$location', '$compile', 'GenerateList', 'SearchWidget', 'PaginateWidget', 'Attr',
    'Icon', 'Column', 'NavigationLink', 'HelpCollapse', 'Button', 'DropDown', 'Empty', 'SelectIcon', 'Store',
    function ($rootScope, $location, $compile, GenerateList, SearchWidget, PaginateWidget, Attr, Icon, Column, NavigationLink,
        HelpCollapse, Button, DropDown, Empty, SelectIcon, Store) {
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
                // Use to inject the form as html into the view.  View MUST have an ng-bind for 'htmlTemplate'.t
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

                $(window).unbind('resize');

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
                        scope[form.name + '_form'][fld].$setValidity('complexity', true);
                        $('#progbar').css({
                            width: 0
                        });
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

            button: Button,

            navigationLink: NavigationLink,


            buildHelpCollapse: function (collapse_array) {
                var html = '',
                    params = {}, i;
                for (i = 0; i < collapse_array.length; i++) {
                    params.hdr = collapse_array[i].hdr;
                    params.content = collapse_array[i].content;
                    params.idx = this.accordion_count++;
                    params.show = (collapse_array[i].show) ? collapse_array[i].show : null;
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
                        html += (field.labelBind) ? "ng-bind=\"" + field.labelBind + "\" " : "";
                        if (horizontal || field.labelClass) {
                            html += "class=\"";
                            html += (field.labelClass) ? field.labelClass : "";
                            html += (horizontal) ? " " + getLabelWidth() : "";
                            html += "\" ";
                        }
                        html += (field.labelNGClass) ? "ng-class=\"" + field.labelNGClass + "\" " : "";
                        html += "for=\"" + fld + '">';
                        html += (field.icon) ? Icon(field.icon) : "";
                        html += "<span class=\"label-text\">" + field.label + "</span>";
                        html += (field.awPopOver && !field.awPopOverRight) ? Attr(field, 'awPopOver', fld) : "";
                        html += "</label>\n";
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
                    html += "<div class=\"form-group\" ";
                    html += (field.ngShow) ? this.attr(field, 'ngShow') : "";
                    html += (field.ngHide) ? this.attr(field, 'ngHide') : "";
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
                            html += (field.chkPass) ? "chk-pass " : "";
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
                            html += (field.ask) ? "ng-disabled=\"" + fld + "_ask\" " : "";
                            html += (field.autocomplete !== undefined) ? this.attr(field, 'autocomplete') : "";
                            html += (field.awRequiredWhen) ? "data-awrequired-init=\"" + field.awRequiredWhen.init + "\" aw-required-when=\"" +
                                field.awRequiredWhen.variable + "\" " : "";
                            html += (field.awValidUrl) ? "aw-valid-url " : "";
                            html += (field.associated && this.form.fields[field.associated].ask) ? "ng-disabled=\"" + field.associated + "_ask\" " : "";
                            html += (field.awMultiselect) ? "aw-multiselect=\"" + field.awMultiselect + "\" " : "";
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
                            html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.required\">A value is required!</div>\n";
                        }
                        if (field.type === "email") {
                            html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.email\">A valid email address is required!</div>\n";
                        }
                        if (field.awPassMatch) {
                            html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld +
                                ".$error.awpassmatch\">Must match Password value</div>\n";
                        }
                        if (field.awValidUrl) {
                            html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld +
                                ".$error.awvalidurl\">URL must begin with ssh, http or https and may not contain '@'</div>\n";
                        }

                        html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";

                        if (field.chkPass) {
                            // complexity error
                            html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld +
                                ".$error.complexity\">Password must be stronger</div>\n";

                            // progress bar
                            html += "<div class=\"pw-progress\">\n";
                            html += "<div class=\"progress progress-striped\">\n";
                            html += "<div id=\"progbar\" class=\"progress-bar\" role=\"progress\"></div>\n";
                            html += "</div>\n";

                            // help panel
                            html += HelpCollapse({
                                hdr: 'Password Complexity',
                                content: "<p>A password with reasonable strength is required. As you type the password " +
                                    "a progress bar will measure the strength. Sufficient strength is reached when the bar turns green.</p>" +
                                    "<p>Password strength is judged using the following:</p>" +
                                    "<ul class=\"pwddetails\">" +
                                    "<li>Minimum 8 characters in length</li>\n" +
                                    "<li>Contains a sufficient combination of the following items:\n" +
                                    "<ul>\n" +
                                    "<li>UPPERCASE letters</li>\n" +
                                    "<li>Numbers</li>\n" +
                                    "<li>Symbols _!@#$%^&*()</li>\n" +
                                    "</ul>\n" +
                                    "</li>\n" +
                                    "</ul>\n",
                                idx: this.accordion_count++,
                                show: null
                            });
                            html += "</div><!-- pw-progress -->\n";
                        }

                        // Add help panel(s)
                        html += (field.helpCollapse) ? this.buildHelpCollapse(field.helpCollapse) : '';

                        html += "</div>\n";
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
                        html += (field.readonly || field.showonly) ? "readonly " : "";
                        html += "aw-watch ></textarea>\n";

                        // Add error messages
                        if ((options.mode === 'add' && field.addRequired) || (options.mode === 'edit' && field.editRequired)) {
                            html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.required\">A value is required!</div>\n";
                        }
                        html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
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
                        html += this.attr(field, 'ngOptions');
                        html += (field.ngChange) ? this.attr(field, 'ngChange') : "";
                        html += buildId(field, fld, this.form);
                        html += (options.mode === 'edit' && field.editRequired) ? "required " : "";
                        html += (options.mode === 'add' && field.addRequired) ? "required " : "";
                        html += (field.multiSelect) ? "multiple " : "";
                        html += (field.readonly) ? "disabled " : "";
                        html += (field.awRequiredWhen) ? "data-awrequired-init=\"" + field.awRequiredWhen.init + "\" aw-required-when=\"" +
                            field.awRequiredWhen.variable + "\" " : "";
                        html += ">\n";
                        html += "<option value=\"\">";
                        html += (field.defaultOption) ? field.defaultOption : "Choose a " + field.label.toLowerCase();
                        html += "</option>\n";
                        html += "</select>\n";
                        // Add error messages
                        if ((options.mode === 'add' && field.addRequired) || (options.mode === 'edit' && field.editRequired) ||
                            field.awRequiredWhen) {
                            html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.required\">A value is required!</div>\n";
                        }
                        html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";

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
                            html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.required\">A value is required!</div>\n";
                        }
                        if (field.integer) {
                            html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.integer\">Must be an integer value</div>\n";
                        }
                        if (field.min !== undefined || field.max !== undefined) {
                            html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.min || " +
                                this.form.name + '_form.' + fld + ".$error.max\">Must be an integer between " + field.min + " and ";
                            html += (field.max !== undefined) ? field.max : 'unlimited';
                            html += "</div>\n";
                        }
                        html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
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
                            html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.required\">A value is required!</div>\n";
                        }
                        if (field.integer) {
                            html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.integer\">Must be an integer value</div>\n";
                        }
                        if (field.min || field.max) {
                            html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.min || " +
                                this.form.name + '_form.' + fld + ".$error.max\">Must be in range " + field.min + " to " +
                                field.max + "</div>\n";
                        }
                        html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
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
                        html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
                        html += "</div><!-- checkbox -->\n";

                        if (horizontal) {
                            html += "</div>\n";
                        }
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
                            html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.required\">A value is required!</div>\n";
                        }
                        html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";

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
                        html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
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
                        html += "><i class=\"fa fa-search\"></i></button>\n";
                        html += "</span>\n";
                        html += "<input type=\"text\" class=\"form-control input-medium lookup\" ";
                        html += "ng-model=\"" + field.sourceModel + '_' + field.sourceField + "\" ";
                        html += "name=\"" + field.sourceModel + '_' + field.sourceField + "\" ";
                        html += "class=\"form-control\" ";
                        html += (field.ngChange) ? this.attr(field, 'ngChange') : "";
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
                            html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' +
                                field.sourceModel + '_' + field.sourceField + ".$dirty && " +
                                this.form.name + '_form.' + field.sourceModel + '_' + field.sourceField +
                                ".$error.required\">A value is required!</div>\n";
                        }
                        html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' +
                            field.sourceModel + '_' + field.sourceField + ".$dirty && " +
                            this.form.name + '_form.' + field.sourceModel + '_' + field.sourceField +
                            ".$error.awlookup\">Value not found</div>\n";
                        html += "<div class=\"error api-error\" ng-bind=\"" + field.sourceModel + '_' + field.sourceField +
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
                        html += this.button({ btn: this.form.actions[action], action: action, toolbar: true });
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
                    tab, sectionShow, offset, width;

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
                        html += "<div class=\"well\">\n";
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

                                // Build button HTML
                                html += "<button type=\"button\" ";
                                html += "class=\"btn btn-sm";
                                html += (button['class']) ? " " + button['class'] : "";
                                html += "\" ";
                                html += "id=\"" + this.form.name + "_" + btn + "_btn\" ";

                                if (button.ngClick) {
                                    html += this.attr(button, 'ngClick');
                                }
                                if (button.ngDisabled) {
                                    if (btn !== 'reset') {
                                        //html += "ng-disabled=\"" + this.form.name + "_form.$pristine || " + this.form.name + "_form.$invalid";
                                        html += "ng-disabled=\"" + this.form.name + "_form.$invalid";
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

                //console.log(html);

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
                        action: act,
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

                html += "<tr ng-repeat=\"" + collection.iterator + " in " + itm + "\" >\n";
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
                    html += "<a ";
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