/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

   /**
 * @ngdoc function
 * @name helpers.function:License
 * @description    Routines for checking and reporting license status
 *          CheckLicense.test() is called in app.js, in line 532, which is when the license is checked. The license information is
 *          stored in local storage using 'Store()'.
 *
 *
 *
 *
*/

import 'tower/forms';

export default
    angular.module('LicenseHelper', ['RestServices', 'Utilities', 'LicenseUpdateFormDefinition',
    'FormGenerator', 'ParseHelper', 'ModalDialog', 'VariablesHelper', 'LicenseFormDefinition',
    'AccessHelper'])


    .factory('CheckLicense', ['$rootScope', '$compile', 'CreateDialog', 'Store',
    'LicenseUpdateForm', 'GenerateForm', 'TextareaResize', 'ToJSON', 'GetBasePath',
    'Rest', 'ProcessErrors', 'Alert', 'IsAdmin', '$location',
    function($rootScope, $compile, CreateDialog, Store, LicenseUpdateForm, GenerateForm,
        TextareaResize, ToJSON, GetBasePath, Rest, ProcessErrors, Alert, IsAdmin, $location) {
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

                var title, html,
                    contact_us = "<a href=\"http://www.ansible.com/contact-us\" target=\"_black\">contact us <i class=\"fa fa-external-link\"></i></a>",
                    renew = "<a href=\"http://www.ansible.com/renew\" target=\"_blank\">ansible.com/renew <i class=\"fa fa-external-link\"></i></a>",
                    pricing = "<a href=\"http://www.ansible.com/pricing\" target=\"_blank\">ansible.com/pricing <i class=\"fa fa-external-link\"></i></a>",
                    license_link = "<a href=\"http://www.ansible.com/license\" target=\"_blank\">click here</a>",
                    result = {},
                    license_is_valid=false;

                if (license && typeof license === 'object' && Object.keys(license).length > 0 && license.valid_key !== undefined) {
                    // we have a license
                    if (!license.valid_key) {
                        title = "Invalid License";
                        html = "<div id=\"license-notification-body\"><div style=\"margin-top:5px; margin-bottom:25px;\"><p>The Ansible Tower license is invalid.</p>";
                    }
                    else if (this.getRemainingDays(license.time_remaining) <= 0) {
                        title = "License Expired";
                        html = "<div id=\"license-notification-body\"><div style=\"margin-top:5px; margin-bottom:25px;\">\n" +
                            "<p>Thank you for using Ansible Tower. The Ansible Tower license has expired</p>";
                        if (parseInt(license.grace_period_remaining,10) > 86400) {
                            // trial licenses don't get a grace period
                            if (license.trial) {
                                html += "<p>Don't worry &mdash; your existing history and content has not been affected, but playbooks will no longer run and new hosts cannot be added. " +
                                    "If you are ready to upgrade, " + contact_us + " or visit " + pricing + " to see all of your license options. Thanks!</p>";
                            } else {
                                html += "<p>Don't worry &mdash; your existing history and content has not been affected, but in " + this.getRemainingDays(license.grace_period_remaining) + " days playbooks will no longer " +
                                    "run and new hosts cannot be added. If you are ready to upgrade, " + contact_us + " " +
                                    "or visit <a href=\"http://www.ansible.com/pricing\" target=\"_blank\">ansible.com/pricing <i class=\"fa fa-external-link\"></i></a> to see all of your license options. Thanks!</p>";
                            }
                        } else {
                            html += "<p>Don’t worry &mdash; your existing history and content has not been affected, but playbooks will no longer run and new hosts cannot be added. If you are ready to renew or upgrade, contact us " +
                                "at " + renew + ". Thanks!</p>";
                        }
                    }
                    else if (this.getRemainingDays(license.time_remaining) < 15) {
                        // Warning: license expiring in less than 15 days
                        title = "License Warning";
                        html = "<div id=\"license-notification-body\"><div style=\"margin-top:5px; margin-bottom:25px;\"><p>Thank you for using Ansible Tower. The Ansible Tower license " +
                            "has " +  this.getRemainingDays(license.time_remaining) + " days remaining.</p>";
                        // trial licenses don't get a grace period
                        if (license.trial) {
                            html += "<p>After this license expires, playbooks will no longer run and hosts cannot be added.  If you are ready to upgrade, " + contact_us + " or visit " + pricing + " to see all of your license options. Thanks!</p>";
                        } else {
                            html += "<p>After this license expires, playbooks will no longer run and hosts cannot be added.  If you are ready to renew or upgrade, contact us at " + renew + ". Thanks!</p>";
                        }

                        // If there is exactly one day remaining, change "days remaining"
                        // to "day remaining".
                        html = html.replace('has 1 days remaining', 'has 1 day remaining');
                    }
                    else if (license.free_instances <= 0) {
                        title = "Host Count Exceeded";
                        html = "<div id=\"license-notification-body\"><div style=\"margin-top:5px; margin-bottom:25px;\"><p>The Ansible Tower license has reached capacity for the number of managed hosts allowed. No new hosts can be added. Existing " +
                            "playbooks can still be run against hosts already in inventory.</p>" +
                            "<p>If you are ready to upgrade, contact us at " + renew + ". Thanks!</p>";

                    } else {
                        // license is valid. the following text is displayed in the license viewer
                        title = "Update License";
                        html = "<div id=\"license-notification-body\"><div style=\"margin-top:5px; margin-bottom:25px;\"><p>The Ansible Tower license is valid.</p>" +
                            "<p>If you are ready to upgrade, contact us at " + renew + ". Thanks!</p>";
                        license_is_valid = true;
                    }
                } else {
                    // No license
                    title = "Add Your License";
                    html = "<div id=\"license-notification-body\"><div style=\"margin-top:5px; margin-bottom:25px;\"><p>Now that you’ve successfully installed or upgraded Ansible Tower, the next step is to add a license file. " +
                        "If you don’t have a license file yet, " + license_link + " to see all of our free and paid license options.</p>" +
                        "<p style=\"margin-top:15px; margin-bottom 15px; text-align:center;\"><a href=\"http://ansible.com/license\" target=\"_blank\" class=\"btn btn-danger free-button\">Get a Free Tower Trial License</a></p>";
                }

                if (IsAdmin()) {
                    html += "<p>Copy and paste the contents of the new license file in the field below and click the Submit button.</p>";
                } else {
                    html += "<p>A system administrator can install the new license by choosing View License on the Account Menu and clicking on the Update License tab.</p>";
                }

                html += "</div>";

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
                json_data.eula_accepted = scope.eula_agreement;
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
                            $location.path('/home');
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
                    scope;

                self.scope = $rootScope.$new();
                scope = self.scope;

                if (license && typeof license === 'object' && Object.keys(license).length > 0) {
                    if (license.tested) {
                        return true;
                    }
                    license.tested = true;
                    Store('license',license);  //update with tested flag
                }

                // Don't do anything when the license is valid
                if (!notify) {
                    return true; // if the license is valid it would exit 'test' here, otherwise it moves on to making the modal for the license
                }

                $location.path('/license');
            },

            GetLicense: function(callback, inScope) {
                // Retrieve license detail
                var self = this,
                    scope = (inScope) ? inScope : self.scope,
                    url = GetBasePath('config');
                Rest.setUrl(url);
                Rest.get()
                    .success(function (data) {
                        if (scope && callback) {
                            scope.$emit(callback, data);
                        }
                        else if (scope) {
                            scope.$emit('CheckLicenseReady', data);
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
