
/******************************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  helpers/License.js
 *
 *  Routines for checking and reporting license status
 *
 */

'use strict';

angular.module('LicenseHelper', ['RestServices', 'Utilities', 'LicenseUpdateFormDefinition', 'FormGenerator', 'ParseHelper', 'ModalDialog', 'VariablesHelper', 'LicenseFormDefinition', 'AccessHelper'])


.factory('CheckLicense', ['$rootScope', '$compile', 'CreateDialog', 'Store', 'LicenseUpdateForm', 'GenerateForm', 'TextareaResize', 'ToJSON', 'GetBasePath', 'Rest', 'ProcessErrors', 'Alert', 'IsAdmin',
function($rootScope, $compile, CreateDialog, Store, LicenseUpdateForm, GenerateForm, TextareaResize, ToJSON, GetBasePath, Rest, ProcessErrors, Alert, IsAdmin) {
    return {
        getRemainingDays: function(time_remaining) {
            // assumes time_remaining will be in seconds
            var tr = parseInt(time_remaining, 10);
            return Math.floor(tr / 86400);
        },

        shouldNotify: function(license) {
            if (license && typeof license === 'object' && Object.keys(license).length > 0) {
                // we have a license object
                if (!license.valid_key) {
                    // missing valid key
                    return true;
                }
                else if (license.free_instances <= 0) {
                    // host count exceeded
                    return true;
                }
                else if (this.getRemainingDays(license.time_remaining) < 15) {
                    // below 15 days remaining on license
                    return true;
                }
                return false;
            } else {
                // missing license object
                return true;
            }
        },

        isAdmin: function() {
            return IsAdmin();
        },

        getHTML: function(license, includeFormButton) {

            var title, html, result = {}, license_is_valid=false;

            if (license && typeof license === 'object' && Object.keys(license).length > 0 && license.valid_key !== undefined) {
                // we have a license
                if (!license.valid_key) {
                    title = "Invalid License";
                    html = "<div id=\"license-notification-body\"><div style=\"margin-top:5px; margin-bottom:25px;\"><p>The Ansible Tower license is invalid.</p>";
                }
                else if (this.getRemainingDays(license.time_remaining) <= 0) {
                    if (parseInt(license.grace_period_remaining,10) > 86400) {
                        title = "License Expired";
                        html = "<div id=\"license-notification-body\"><div style=\"margin-top:5px; margin-bottom:25px;\"><p>Thank you for using Ansible Tower. The Ansible Tower license " +
                        "has expired. You will no longer be able to add managed hosts or run playbooks after " + this.getRemainingDays(license.grace_period_remaining) + " days</p>";
                    } else {
                        title = "License Expired";
                        html = "<div id=\"license-notification-body\"><div style=\"margin-top:5px; margin-bottom:25px;\"><p>Thank you for using Ansible Tower. The Ansible Tower license " +
                        "has expired, and the 30 day grace period has been exceeded. To continue using Tower to run playbooks and add managed hosts a " +
                        "valid license key is required.</p>";
                    }
                }
                else if (this.getRemainingDays(license.time_remaining) < 15) {
                    title = "License Warning";
                    html = "<div id=\"license-notification-body\"><div style=\"margin-top:5px; margin-bottom:25px;\"><p>Thank you for using Ansible Tower. The Ansible Tower license " +
                        "has " +  this.getRemainingDays(license.time_remaining) + " days remaining. Once the license expires you will no longer be able to add managed hosts or run playbooks.</p>";
                }
                else if (license.free_instances <= 0) {
                    title = "Host Count Exceeded";
                    html = "<div id=\"license-notification-body\"><div style=\"margin-top:5px; margin-bottom:25px;\"><p>The Ansible Tower license has reached capacity for the number of " +
                        "managed hosts allowed. No additional hosts can be added.</p>";
                } else {
                    // license is valid. the following text is displayed in the license viewer
                    title = "Update License";  // not actually used
                    html = "<div id=\"license-notification-body\"><div style=\"margin-top:5px; margin-bottom:25px;\"><p>The Ansible Tower license is valid.</p>";
                    license_is_valid = true;
                }
            } else {
                // No license
                title = "License Required";
                html = "<div id=\"license-notification-body\"><div style=\"margin-top:5px; margin-bottom:25px;\"><p>Thank you for trying Ansible Tower. Without a valid license you will not be able to add managed hosts or " +
                    "run playbooks. A <strong>FREE</strong> trial license is available for various infrastructure sizes, as well as free unlimited use for up to ten nodes.</p>";
            }

            if (IsAdmin()) {
                if (license_is_valid) {
                    html += "<p>If you need to update or extend the Ansible Tower license, please visit <a href=\"http://ansible.com/license\" target=\"_blank\">ansible.com/license</a>. " +
                        "Copy and paste the new license key in the field below and click the Submit button.</p>";
                } else {
                    html += "<p>Please visit <a href=\"http://ansible.com/license\" target=\"_blank\">ansible.com/license</a> to obtain a valid license key. " +
                        "Copy and paste the license key in the field below and click the Submit button.";
                }
            } else {
                if (license_is_valid) {
                    html += "<p>If you need to update or extend the Ansible Tower license, please visit <a href=\"http://ansible.com/license\" target=\"_blank\">ansible.com/license</a>. A system administrator " +
                        "can install the new license by choosing View License on the Account Menu and clicking on the Update License tab.";
                } else {
                    html += "<p>Please visit <a href=\"http://ansible.com/license\" target=\"_blank\">ansible.com/license</a> to obtain a valid license key. A system administrator " +
                        "can install the new license by choosing View License on the Account Menu and clicking on the Update License tab.";
                }
            }
            html += "</p></div>";

            if (IsAdmin()) {
                html += GenerateForm.buildHTML(LicenseUpdateForm, { mode: 'edit', showButtons:((includeFormButton) ? true : false), breadCrumbs: false });
            }
            html += "</div>";

            result.body = html;
            result.title = title;
            return result;
        },

        postLicense: function(license_key, in_scope) {
            var url = GetBasePath('config'),
                self = this,
                json_data, scope;

            scope = (in_scope) ? in_scope : self.scope;

            json_data = ToJSON('json', license_key);
            if (typeof json_data === 'object' && Object.keys(json_data).length > 0) {
                Rest.setUrl(url);
                Rest.post(json_data)
                    .success(function () {
                        try {
                            $('#license-modal-dialog').dialog('close');
                        }
                        catch(e) {
                            // ignore
                        }
                        Alert('License Accepted', 'The Ansible Tower license was updated. To view or update license information in the future choose View License from the Account menu.','alert-info');
                    })
                    .error(function (data, status) {
                        scope.license_json_api_error = "A valid license key in JSON format is required";
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to update license. POST returned: ' + status
                        });
                    });
            } else {
                scope.license_json_api_error = "A valid license key in JSON format is required";
            }
        },

        test: function() {
            var license = Store('license'),
                notify = this.shouldNotify(license),
                self = this,
                scope, height, html, buttons, submitKey;

            self.scope = $rootScope.$new();
            scope = self.scope;

            submitKey = this.postLicense;

            if (license && typeof license === 'object' && Object.keys(license).length > 0) {
                if (license.tested) {
                    return true;
                }
                license.tested = true;
                Store('license',license);  //update with tested flag
            }

            // Don't do anything when the license is valid
            if (!notify) {
                return true;
            }

            html = this.getHTML(license);
            $('#license-modal-dialog').html(html.body);

            scope.flashMessage = null;
            scope.parseType = 'json';
            scope.license_json = " ";

            scope.removeLicenseDialogReady = scope.$on('LicenseDialogReady', function() {
                var e = angular.element(document.getElementById('license-modal-dialog'));
                $compile(e)(scope);
                $('#license-modal-dialog').dialog('open');
            });

            scope.submitLicenseKey = function() {
                submitKey(scope.license_json);
            };

            if (IsAdmin()) {
                buttons = [{
                    label: "Cancel",
                    onClick: function() {
                        $('#license-modal-dialog').dialog('close');
                    },
                    "class": "btn btn-default",
                    "id": "license-cancel-button"
                }, {
                    label: "Submit",
                    onClick: function() {
                        scope.submitLicenseKey();
                    },
                    "class": "btn btn-primary",
                    "id": "license-submit-button"
                }];
            } else {
                buttons = [{
                    label: "OK",
                    onClick: function() {
                        $('#license-modal-dialog').dialog('close');
                    },
                    "class": "btn btn-primary",
                    "id": "license-ok-button"
                }];
            }

            height = (IsAdmin()) ? 600 : 350;

            CreateDialog({
                scope: scope,
                buttons: buttons,
                width: 700,
                height: height,
                minWidth: 400,
                title: html.title,
                id: 'license-modal-dialog',
                clonseOnEscape: false,
                onClose: function() {
                    if (scope.codeMirror) {
                        scope.codeMirror.destroy();
                    }
                    $('#license-modal-dialog').empty();
                },
                onResizeStop: function() {
                    if (IsAdmin()) {
                        TextareaResize({
                            scope: scope,
                            textareaId: 'license_license_json',
                            modalId: 'license-modal-dialog',
                            formId: 'license-notification-body',
                            fld: 'license_json',
                            parse: true,
                            onChange: function() { scope.license_json_api_error = ''; }
                        });
                    }
                },
                onOpen: function() {
                    if (IsAdmin()) {
                        setTimeout(function() {
                            TextareaResize({
                                scope: scope,
                                textareaId: 'license_license_json',
                                modalId: 'license-modal-dialog',
                                formId: 'license-notification-body',
                                fld: 'license_json',
                                parse: true,
                                onChange: function() { scope.license_json_api_error = ''; }
                            });
                            $('#cm-license_json-container .CodeMirror textarea').focus();
                        }, 300);
                    } else {
                        $('#license-ok-button').focus();
                    }
                },
                callback: 'LicenseDialogReady'
            });
        }
    };
}])

.factory('LicenseViewer', ['$location', '$rootScope', '$compile', 'GenerateForm', 'Rest', 'Alert', 'GetBasePath', 'ProcessErrors', 'FormatDate', 'Prompt', 'Empty', 'LicenseForm', 'IsAdmin', 'CreateDialog', 'CheckLicense', 'TextareaResize',
function ($location, $rootScope, $compile, GenerateForm, Rest, Alert, GetBasePath, ProcessErrors, FormatDate, Prompt, Empty, LicenseForm, IsAdmin, CreateDialog, CheckLicense, TextareaResize) {
    return {

        createDialog: function(html) {
            var self = this,
                scope = this.getScope(),
                buttons;

            if (scope.removeLicenseDialogReady) {
                scope.removeLicenseDialogReady();
            }
            scope.removeLicenseDialogReady = scope.$on('LicenseDialogReady', function() {
                var e, h;

                e = angular.element(document.getElementById('license-modal-dialog'));
                e.empty().html(html);

                if (scope.license_status === 'Invalid License Key') {
                    $('#license_tabs li:eq(1)').hide();
                }

                scope.parseType = 'json';
                scope.license_json = " ";
                h = CheckLicense.getHTML(self.getLicense(),true).body;
                $('#license-modal-dialog #license_tabs').append("<li><a id=\"update_license_link\" ng-click=\"toggleTab($event, 'update_license_link', 'license_tabs')\" href=\"#update_license\" data-toggle=\"tab\">Update License</a></li>");
                $('#license-modal-dialog .tab-content').append("<div class=\"tab-pane\" id=\"update_license\"></div>");
                $('#license-modal-dialog #update_license').html(h);

                setTimeout(function() {
                    $compile(e)(scope);
                    $('#license-modal-dialog').dialog('open');
                }, 300);
            });

            scope.submitLicenseKey = function() {
                CheckLicense.postLicense(scope.license_json, scope);
            };

            buttons = [{
                label: "OK",
                onClick: function() {
                    $('#license-modal-dialog').dialog('close');
                },
                "class": "btn btn-primary",
                "id": "license-ok-button"
            }];

            CreateDialog({
                scope: scope,
                buttons: buttons,
                width: 700,
                height: 600,
                minWidth: 400,
                title: 'Ansible Tower License',
                id: 'license-modal-dialog',
                clonseOnEscape: false,
                onClose: function() {
                    if (scope.codeMirror) {
                        scope.codeMirror.destroy();
                    }
                    $('#license-modal-dialog').empty();
                },
                onResizeStop: function() {
                    if (IsAdmin()) {
                        TextareaResize({
                            scope: scope,
                            textareaId: 'license_license_json',
                            modalId: 'license-modal-dialog',
                            formId: 'license-notification-body',
                            fld: 'license_json',
                            bottom_margin: 90,
                            parse: true,
                            onChange: function() { scope.license_json_api_error = ''; }
                        });
                    }
                },
                onOpen: function() {
                    if (IsAdmin()) {
                        setTimeout(function() {
                            TextareaResize({
                                scope: scope,
                                textareaId: 'license_license_json',
                                modalId: 'license-modal-dialog',
                                formId: 'license-notification-body',
                                fld: 'license_json',
                                parse: true,
                                bottom_margin: 90,
                                onChange: function() { scope.license_json_api_error = ''; }
                            });
                        }, 300);
                    }
                    $('#license-ok-button').focus();
                    $('#update_license_link').on('click', function() {
                        if (IsAdmin()) {
                            TextareaResize({
                                scope: scope,
                                textareaId: 'license_license_json',
                                modalId: 'license-modal-dialog',
                                formId: 'license-notification-body',
                                fld: 'license_json',
                                bottom_margin: 90,
                                parse: true,
                                onChange: function() { scope.license_json_api_error = ''; }
                            });
                        }
                    });
                },
                callback: 'LicenseDialogReady'
            });
        },

        getDefaultHTML: function(license_info) {
            var fld, html,
                self = this,
                generator = GenerateForm;

            self.form = angular.copy(LicenseForm);

            for (fld in self.form.fields) {
                if (fld !== 'time_remaining' && fld !== 'license_status') {
                    if (Empty(license_info[fld])) {
                        delete self.form.fields[fld];
                    }
                }
            }

            if (!IsAdmin()) {
                delete self.form.fields.license_key;
            }

            if (license_info.is_aws || Empty(license_info.license_date)) {
                delete self.form.fields.license_date;
                delete self.form.fields.time_remaining;
            }

            html = generator.buildHTML(self.form, { mode: 'edit', showButtons: false, breadCrumbs: false });
            return html;
        },

        loadDefaultScope: function(license_info) {
            var fld, dt, days, remainder, hours, minutes, seconds, license,
                self = this,
                scope = this.getScope();

            for (fld in self.form.fields) {
                if (!Empty(license_info[fld])) {
                    scope[fld] = license_info[fld];
                }
            }

            if (scope.license_date) {
                dt = new Date(parseInt(scope.license_date, 10) * 1000); // expects license_date in seconds
                scope.license_date = FormatDate(dt);
                scope.time_remaining = scope.time_remaining * 1000;
                days = parseInt(scope.time_remaining / 86400000, 10);
                remainder = scope.time_remaining - (days * 86400000);
                hours = parseInt(remainder / 3600000, 10);
                remainder = remainder - (hours * 3600000);
                minutes = parseInt(remainder / 60000, 10);
                remainder = remainder - (minutes * 60000);
                seconds = parseInt(remainder / 1000, 10);
                scope.time_remaining = days + ' days ' + ('0' + hours).slice(-2) + ':' + ('0' + minutes).slice(-2) + ':' +
                  ('0' + seconds).slice(-2);
            }

            if (parseInt(scope.free_instances) <= 0) {
                scope.free_instances_class = 'field-failure';
            } else {
                scope.free_instances_class = 'field-success';
            }

            license = license_info;
            if (license.valid_key === undefined) {
                scope.license_status = 'Missing License Key';
                scope.status_color = 'license-invalid';
            } else if (!license.valid_key) {
                scope.license_status = 'Invalid License Key';
                scope.status_color = 'license-invalid';
            } else if (license.date_expired !== undefined && license.date_expired) {
                scope.license_status = 'License Expired';
                scope.status_color = 'license-expired';
            } else if (license.date_warning !== undefined && license.date_warning) {
                scope.license_status = 'License Expiring Soon';
                scope.status_color = 'license-warning';
            } else if (license.free_instances !== undefined && parseInt(license.free_instances) <= 0) {
                scope.license_status = 'No Available Managed Hosts';
                scope.status_color = 'license-invalid';
            } else {
                scope.license_status = 'Valid License';
                scope.status_color = 'license-valid';
            }
        },

        getScope: function() {
            return this.scope;
        },

        setLicense: function(license_info) {
            this.license = license_info;
        },

        getLicense: function() {
            return this.license;
        },

        showViewer: function() {
            var self = this,
                scope = self.scope = $rootScope.$new();

            if (scope.removeLicenseDataReady) {
                scope.removeLicenseDataReady();
            }
            scope.removeLicenseDataReady = scope.$on('LicenseDataReady', function(e, data) {
                data.license_info.tower_version = data.version;
                self.setLicense(data.license_info);
                var html = self.getDefaultHTML(data.license_info);
                self.loadDefaultScope(data.license_info);
                self.createDialog(html);
            });
            self.GetLicense();
        },

        GetLicense: function(callback) {
            // Retrieve license detail
            var scope = this.getScope(),
                url = GetBasePath('config');
            Rest.setUrl(url);
            Rest.get()
                .success(function (data) {
                    if (scope && callback) {
                        scope.$emit(callback, data);
                    }
                    else if (scope) {
                        scope.$emit('LicenseDataReady', data);
                    }
                })
                .error(function (data, status) {
                    ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to retrieve license. GET status: ' + status
                    });
                });
        }
    };
}]);

/*
.factory('CheckLicense', ['$rootScope', 'Store', 'Alert', '$location', 'Authorization',
    function ($rootScope, Store, Alert, $location, Authorization) {
        return function () {
            // Check license status and alert the user, if needed
            var status = 'success',
                hdr, msg,
                license = Store('license'),
                purchase_msg = '<p>To purchase a license or extend an existing license ' +
                '<a href="http://www.ansible.com/ansible-pricing" target="_blank"><strong>visit the Ansible online store</strong></a>, ' +
                'or visit <strong><a href="https://support.ansible.com" target="_blank">support.ansible.com</a></strong> for assistance.</p>';

            if (license && !Authorization.licenseTested()) {
                // This is our first time evaluating the license
                license.tested = true;
                Store('license',license);  //update with tested flag
                $rootScope.license_tested = true;
                $rootScope.version = license.version;
                if (license.valid_key !== undefined && license.valid_key === false) {
                    // The license is invalid. Stop the user from logging in.
                    status = 'alert-danger';
                    hdr = 'License Error';
                    msg = '<p>There is a problem with the /etc/awx/license file on your Tower server. Check to make sure Tower can access ' +
                        'the file.</p>' + purchase_msg;
                    Alert(hdr, msg, status, null, false, true);
                } else if (license.demo !== undefined && license.demo === true) {
                    // demo
                    status = 'alert-info';
                    hdr = 'Tower Demo';
                    msg = '<p>Thank you for trying Ansible Tower. You can use this edition to manage up to 10 hosts free.</p>' +
                        purchase_msg;
                    Alert(hdr, msg, status);
                }
                if (license.date_expired !== undefined && license.date_expired === true) {
                    // expired
                    status = 'alert-info';
                    hdr = 'License Expired';
                    msg = '<p>Your Ansible Tower License has expired and is no longer compliant. You can continue, but you will be ' +
                        'unable to add any additional hosts.</p>' + purchase_msg;
                    Alert(hdr, msg, status);
                } else if (license.date_warning !== undefined && license.date_warning === true) {
                    status = 'alert-info';
                    hdr = 'License Warning';
                    msg = '<p>Your Ansible Tower license is about to expire!</p>' + purchase_msg;
                    Alert(hdr, msg, status);
                }
                if (license.free_instances !== undefined && parseInt(license.free_instances) <= 0) {
                    status = 'alert-info';
                    hdr = 'License Warning';
                    msg = '<p>Your Ansible Tower license has reached capacity for the number of managed ' +
                        'hosts allowed. You will not be able to add any additional hosts.</p>' + purchase_msg;
                    Alert(hdr, msg, status, null, true);
                }
            }
        };
    }
]);
*/