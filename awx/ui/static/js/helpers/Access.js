/******************************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  helpers/Access.js
 *
 *  Routines for checking user access and license state
 *
 */

'use strict';

angular.module('AccessHelper', ['RestServices', 'Utilities', 'ngCookies', 'LicenseUpdateFormDefinition', 'FormGenerator', 'ParseHelper', 'ModalDialog', 'VariablesHelper'])

    .factory('CheckAccess', ['$rootScope', 'Alert', 'Rest', 'GetBasePath', 'ProcessErrors',
        function ($rootScope, Alert, Rest, GetBasePath, ProcessErrors) {
            return function (params) {
                // set PermissionAddAllowed to true or false based on user access. admins and org admins are granted
                // accesss.
                var me = $rootScope.current_user,
                    scope = params.scope;

                if (me.is_superuser) {
                    scope.PermissionAddAllowed = true;
                } else {
                    if (me.related.admin_of_organizations) {
                        Rest.setUrl(me.related.admin_of_organizations);
                        Rest.get()
                            .success(function (data) {
                                if (data.results.length > 0) {
                                    scope.PermissionAddAllowed = true;
                                } else {
                                    scope.PermissionAddAllowed = false;
                                }
                            })
                            .error(function (data, status) {
                                ProcessErrors(scope, data, status, null, {
                                    hdr: 'Error!',
                                    msg: 'Call to ' + me.related.admin_of_organizations +
                                        ' failed. DELETE returned status: ' + status
                                });
                            });
                    }
                }
                //if (!access) {
                //   Alert('Access Denied', 'You do not have access to this function. Please contact your system administrator.');
                //}
                //return access;
            };
        }
    ])

.factory('CheckLicense', ['$rootScope', '$compile', 'CreateDialog', 'Store', 'LicenseUpdateForm', 'GenerateForm', 'TextareaResize', 'ToJSON', 'GetBasePath', 'Rest', 'ProcessErrors', 'Alert',
function($rootScope, $compile, CreateDialog, Store, LicenseUpdateForm, GenerateForm, TextareaResize, ToJSON, GetBasePath, Rest, ProcessErrors, Alert) {
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

        getHTML: function(license) {
            var title, html, result = {};
            if (license && typeof license === 'object' && Object.keys(license).length > 0 && license.valid_key !== undefined) {
                // we have a license
                if (!license.valid_key) {
                    title = "Invalid License";
                    html = "<div id=\"license-notification-body\"><div style=\"margin-top:5px; margin-bottom:25px;\"><p>The Ansible Tower license is invalid. Please visit " +
                        "<a href=\"http://ansible.com/license\" target=\"_blank\">http://ansible.com/license</a> to obtain a valid license key. " +
                        "Copy and paste the key in the field below and click the Submit button.</p></div>";
                }
                else if (this.getRemainingDays(license.time_remaining) <= 0) {
                    if (parseInt(license.grace_period_remaining,10) > 86400) {
                        title = "License Expired";
                        html = "<div id=\"license-notification-body\"><div style=\"margin-top:5px; margin-bottom:25px;\"><p>Thank you for using Ansible Tower. The Ansible Tower license " +
                        "has expired. You will no longer be able to run playbooks after " + this.getRemainingDays(license.grace_period_remaining) + " days</p>" +
                        "<p>Please visit <a href=\"http://ansible.com/license\" target=\"_blank\">ansible.com/license</a> to purchse a valid license. " +
                        "Copy and paste the new license key in the field below and click the Submit button.</p></div>";
                    } else {
                        title = "License Expired";
                        html = "<div id=\"license-notification-body\"><div style=\"margin-top:5px; margin-bottom:25px;\"><p>Thank you for using Ansible Tower. The Ansible Tower license " +
                        "has expired, and the 30 day grace period has been exceeded. To continue using Tower to run playbooks and adding managed hosts a " +
                        "valid license key is required.</p><p>Please visit <a href=\"ansible.com/license\" target=\"_blank\">http://ansible.com/license</a> to " +
                        "purchse a license. Copy and paste the new license key in the field below and click the Submit button.</p>";
                    }
                }
                else if (this.getRemainingDays(license.time_remaining) < 15) {
                    html = "<div id=\"license-notification-body\"><div style=\"margin-top:5px; margin-bottom:25px;\"><p>Thank you for using Ansible Tower. The Ansible Tower license " +
                        "has " +  this.getRemainingDays(license.time_remaining) + " remaining.</p>" +
                        "<p>Extend your Ansible Tower license by visiting <a href=\"ansible.com/license\" target=\"_blank\">http://ansible.com/license</a>. " +
                        "Copy and paste the new license key in the field below and click the Submit button.</p></div>";
                }
                else if (license.free_instances <= 0) {
                    title = "Host Count Exceeded";
                    html = "<div id=\"license-notification-body\"><div style=\"margin-top:5px; margin-bottom:25px;\"><p>The Ansible Tower license has reached capacity for the number of " +
                        "managed hosts allowed. No additional hosts can be added.</p><p>To extend the Ansible Tower license please visit " +
                        "<a href=\"http://ansible.com/license\" target=\"_blank\">ansible.com/license</a>. " +
                        "Copy and paste the new license key in the field below and click the Submit button.</p>";
                }
            } else {
                // No license
                title = "License Required";
                html = "<div id=\"license-notification-body\"><div style=\"margin-top:5px; margin-bottom:25px;\"><p>Thank you for trying Ansible Tower. A <strong>FREE</strong> trial license is available for various infrastructure sizes, as well as free unlimited use for up to ten nodes.<p>" +
                    "<p>Visit <a href=\"http://ansible.com/license\" target=\"_blank\">ansible.com/license</a> to obtain a free license key. Copy and paste the key in the field below and " +
                    "click the Submit button.</p></div>";
            }
            html += GenerateForm.buildHTML(LicenseUpdateForm, { mode: 'edit', showButtons: true, breadCrumbs: false });
            html += "</div>";
            result.body = html;
            result.title = title;
            return result;
        },

        test: function() {
            var license = Store('license'),
                notify = this.shouldNotify(license),
                html, buttons, scope;

            if (license && typeof license === 'object' && Object.keys(license).length > 0) {
                if (license.tested) {
                    return true;
                }
                license.tested = true;
                Store('license',license);  //update with tested flag
            }

            if (!notify) {
                return true;
            }

            scope = $rootScope.$new();
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
                var url = GetBasePath('config'),
                    json_data = ToJSON(scope.parseType, scope.license_json);
                if (typeof json_data === 'object' && Object.keys(json_data).length > 0) {
                    Rest.setUrl(url);
                    Rest.post(json_data)
                        .success(function () {
                            $('#license-modal-dialog').dialog('close');
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
            };

            buttons = [{
                label: "Cancel",
                onClick: function() {
                    $('#license-modal-dialog').dialog('close');
                },
                "class": "btn btn-default",
                "id": "license-cancel-button"
            }];

            CreateDialog({
                scope: scope,
                buttons: buttons,
                width: 700,
                height: 625,
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
                    TextareaResize({
                        scope: scope,
                        textareaId: 'license_license_json',
                        modalId: 'license-modal-dialog',
                        formId: 'license-notification-body',
                        fld: 'license_json',
                        bottom_margin: 30,
                        parse: true,
                        onChange: function() { scope.license_json_api_error = ''; }
                    });
                },
                onOpen: function() {
                    setTimeout(function() {
                        TextareaResize({
                            scope: scope,
                            textareaId: 'license_license_json',
                            modalId: 'license-modal-dialog',
                            formId: 'license-notification-body',
                            fld: 'license_json',
                            bottom_margin: 30,
                            parse: true,
                            onChange: function() { scope.license_json_api_error = ''; }
                        });
                        $('#cm-license_json-container .CodeMirror textarea').focus();
                    }, 300);
                },
                callback: 'LicenseDialogReady'
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


