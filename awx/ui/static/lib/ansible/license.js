/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * License.js
 *
 * View license info found in /api/vi/config/
 *
 *****************************************/

'use strict';

angular.module('License', ['RestServices', 'Utilities', 'FormGenerator', 'PromptDialog', 'LicenseFormDefinition'])
    .factory('ViewLicense', ['$location', '$rootScope', 'GenerateForm', 'Rest', 'Alert', 'GetBasePath', 'ProcessErrors',
        'FormatDate', 'Prompt', 'Empty', 'LicenseForm',
        function ($location, $rootScope, GenerateForm, Rest, Alert, GetBasePath, ProcessErrors, FormatDate, Prompt, Empty,
            LicenseForm) {
            return function () {

                var defaultUrl = GetBasePath('config'),
                    generator = GenerateForm,
                    form = angular.copy(LicenseForm),
                    scope;

                // Retrieve detail record and prepopulate the form
                Rest.setUrl(defaultUrl);
                Rest.get()
                    .success(function (data) {

                        var fld, dt, days, remainder, hours, minutes, seconds, license;
                        
                        for (fld in form.fields) {
                            if (fld !== 'time_remaining' && fld !== 'license_status') {
                                if (Empty(data.license_info[fld])) {
                                    delete form.fields[fld];
                                }
                            }
                        }

                        if (data.license_info.is_aws || Empty(data.license_info.license_date)) {
                            delete form.fields.license_date;
                            delete form.fields.time_remaining;
                        }

                        scope = generator.inject(form, { mode: 'edit', modal: true, related: false });
                        generator.reset();

                        scope.formModalAction = function () {
                            $('#form-modal').modal("hide");
                        };

                        scope.formModalActionLabel = 'OK';
                        scope.formModalCancelShow = false;
                        scope.formModalInfo = 'Purchase/Extend License';
                        scope.formModalHeader = "Ansible Tower <span class=\"license-version\">v." + data.version + "</span>";

                        // Respond to license button
                        scope.formModalInfoAction = function () {
                            Prompt({
                                hdr: 'Tower Licensing',
                                body: "<p>Ansible Tower licenses can be purchased or extended by visiting <a id=\"license-link\" " +
                                    "href=\"http://www.ansible.com/ansible-pricing\" target=\"_blank\">" +
                                    "the Ansible online store</a>. Would you like to purchase or extend your license now?</p>",
                                'class': 'btn-primary',
                                action: function () {
                                    window.open('http://www.ansible.com/ansible-pricing', 'storeWindow');
                                }
                            });
                        };

                        for (fld in form.fields) {
                            if (!Empty(data.license_info[fld])) {
                                scope[fld] = data.license_info[fld];
                            }
                        }

                        if (scope.license_date) {
                            dt = new Date(parseInt(scope.license_date, 10) * 1000);
                            scope.license_date = FormatDate(dt);

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

                        license = data.license_info;
                        if (license.valid_key !== undefined && !license.valid_key) {
                            scope.license_status = 'Invalid';
                            scope.status_color = 'license-invalid';
                        } else if (license.demo !== undefined && license.demo) {
                            scope.license_status = 'Demo';
                            scope.status_color = 'license-demo';
                        } else if (license.date_expired !== undefined && license.date_expired) {
                            scope.license_status = 'Expired';
                            scope.status_color = 'license-expired';
                        } else if (license.date_warning !== undefined && license.date_warning) {
                            scope.license_status = 'Expiration Warning';
                            scope.status_color = 'license-warning';
                        } else if (license.free_instances !== undefined && parseInt(license.free_instances) <= 0) {
                            scope.license_status = 'No available managed hosts';
                            scope.status_color = 'license-invalid';
                        } else {
                            scope.license_status = 'Valid';
                            scope.status_color = 'license-valid';
                        }

                    })
                    .error(function (data, status) {
                        ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to retrieve license. GET status: ' + status
                        });
                    });
            };
        }
    ]);