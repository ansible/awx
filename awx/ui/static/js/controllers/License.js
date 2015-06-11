/************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 *
 *  Organizations.js
 *
 *  Controller functions for Organization model.
 *
 */
/**
 * @ngdoc function
 * @name controllers.function:Organizations
 * @description This controller's for the Organizations page
*/


export function LicenseController(ClearScope, $location, $rootScope, $compile, $filter, GenerateForm, Rest, Alert,
    GetBasePath, ProcessErrors, FormatDate, Prompt, Empty, LicenseForm, IsAdmin, CreateDialog, CheckLicense,
    TextareaResize, $scope) {

        ClearScope();

        $scope.getDefaultHTML = function(license_info) {
            var fld, html,
                self = this,
                generator = GenerateForm;

            self.form = angular.copy(LicenseForm);

            for (fld in self.form.fields) {
                if (fld !== 'time_remaining' && fld !== 'license_status' && fld !== 'tower_version') {
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
        };

        $scope.loadDefaultScope = function(license_info, version) {
            var fld, dt, days, license,
                self = this;

            for (fld in self.form.fields) {
                if (!Empty(license_info[fld])) {
                    $scope[fld] = license_info[fld];
                }
            }

            $scope.tower_version = version;

            if ($scope.license_date) {
                dt = new Date(parseInt($scope.license_date, 10) * 1000); // expects license_date in seconds
                $scope.license_date = FormatDate(dt);
                $scope.time_remaining = parseInt($scope.time_remaining,10) * 1000;
                if ($scope.time_remaining < 0) {
                    days = 0;
                } else {
                    days = Math.floor($scope.time_remaining / 86400000);
                }
                $scope.time_remaining = (days!==1) ? $filter('number')(days, 0) + ' days' : $filter('number')(days, 0) + ' day'; // '1 day' and '0 days/2 days' or more
            }

            if (parseInt($scope.free_instances) <= 0) {
                $scope.free_instances_class = 'field-failure';
            } else {
                $scope.free_instances_class = 'field-success';
            }

            license = license_info;
            if (license.valid_key === undefined) {
                $scope.license_status = 'Missing License Key';
                $scope.status_color = 'license-invalid';
            } else if (!license.valid_key) {
                $scope.license_status = 'Invalid License Key';
                $scope.status_color = 'license-invalid';
            } else if (license.date_expired !== undefined && license.date_expired) {
                $scope.license_status = 'License Expired';
                $scope.status_color = 'license-expired';
            } else if (license.date_warning !== undefined && license.date_warning) {
                $scope.license_status = 'License Expiring Soon';
                $scope.status_color = 'license-warning';
            } else if (license.free_instances !== undefined && parseInt(license.free_instances) <= 0) {
                $scope.license_status = 'No Available Managed Hosts';
                $scope.status_color = 'license-invalid';
            } else {
                $scope.license_status = 'Valid License';
                $scope.status_color = 'license-valid';
            }
        };

        $scope.setLicense = function(license_info, version) {
            this.license = license_info;
            this.version = version;
        };

        $scope.getLicense = function(){
            return this.license;
        };

        $scope.submitLicenseKey = function() {
            CheckLicense.postLicense($scope.license_json, $scope);
        };

        if ($scope.removeLicenseDataReady) {
            $scope.removeLicenseDataReady();
        }
        $scope.removeLicenseDataReady = $scope.$on('LicenseDataReady', function(e, data) {
            var html, version, eula, h;
            version = data.version.replace(/-.*$/,'');
            $scope.setLicense(data.license_info, version);
            html = $scope.getDefaultHTML(data.license_info);
            $scope.loadDefaultScope(data.license_info, version);
            eula = (data.eula) ? data.eula : "" ;

            e = angular.element(document.getElementById('license-modal-dialog'));
            e.empty().html(html);

            $scope.parseType = 'json';
            $scope.license_json = JSON.stringify($scope.license, null, ' ');
            $scope.eula = eula;
            $scope.eula_agreement = false;


            h = CheckLicense.getHTML($scope.getLicense(),true).body;
            $('#license-modal-dialog #license_tabs').append("<li><a id=\"update_license_link\" ng-click=\"toggleTab($event, 'update_license_link', 'license_tabs')\" href=\"#update_license\" data-toggle=\"tab\">Update License</a></li>");
            $('#license-modal-dialog .tab-content').append("<div class=\"tab-pane\" id=\"update_license\"></div>");
            $('#license-modal-dialog #update_license').html(h);

            if ($scope.license_status === 'Invalid License Key' || $scope.license_status === 'Missing License Key') {
                $('#license_tabs li:eq(1)').hide();
                $('#license_tabs li:eq(2) a').tab('show');
            }

            $('#license_license_json').attr('ng-required' , 'true' );
            $('#license_eula_agreement_chbox').attr('ng-required' , 'true' );
            $('#license_form_submit_btn').attr('ng-disabled' , "license_form.$invalid" );
            e = angular.element(document.getElementById('license-modal-dialog'));
            $compile(e)($scope);

            if (IsAdmin()) {
                setTimeout(function() {
                    TextareaResize({
                        scope: $scope,
                        textareaId: 'license_license_json',
                        modalId: 'license-modal-dialog',
                        formId: 'license-notification-body',
                        fld: 'license_json',
                        parse: true,
                        bottom_margin: 90,
                        onChange: function() { $scope.license_json_api_error = ''; }
                    });
                }, 300);
            }
            $('#license-ok-button').focus();
            $('#update_license_link').on('shown.bs.tab', function() {
                if (IsAdmin()) {
                    TextareaResize({
                        scope: $scope,
                        textareaId: 'license_license_json',
                        modalId: 'license-modal-dialog',
                        formId: 'license-notification-body',
                        fld: 'license_json',
                        bottom_margin: 90,
                        parse: true,
                        onChange: function() { $scope.license_json_api_error = ''; }
                    });
                }
            });
        });
        CheckLicense.GetLicense('LicenseDataReady', $scope);

    }

LicenseController.$inject = ['ClearScope', '$location', '$rootScope', '$compile', '$filter', 'GenerateForm', 'Rest', 'Alert',
'GetBasePath', 'ProcessErrors', 'FormatDate', 'Prompt', 'Empty', 'LicenseForm', 'IsAdmin', 'CreateDialog',
'CheckLicense', 'TextareaResize', '$scope'];
