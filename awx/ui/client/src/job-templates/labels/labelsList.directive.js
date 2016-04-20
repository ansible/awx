/* jshint unused: vars */
export default
    [   'templateUrl',
        'Wait',
        'Rest',
        'GetBasePath',
        'ProcessErrors',
        'Prompt',
        function(templateUrl, Wait, Rest, GetBasePath, ProcessErrors, Prompt) {
            return {
                restrict: 'E',
                scope: false,
                templateUrl: templateUrl('job-templates/labels/labelsList'),
                link: function(scope, element, attrs) {
                    scope.labels = scope.
                        job_template.summary_fields.labels;

                    scope.deleteLabel = function(templateId, templateName, labelId, labelName) {
                        var action = function () {
                            $('#prompt-modal').modal('hide');
                            Wait('start');
                            var url = GetBasePath("job_templates") + templateId + "/labels/";
                            Rest.setUrl(url);
                            Rest.post({"disassociate": true, "id": labelId})
                                .success(function () {
                                    Wait('stop');
                                    scope.search("job_template");
                                })
                                .error(function (data, status) {
                                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                        msg: 'Could not disacssociate label from JT.  Call to ' + url + ' failed. DELETE returned status: ' + status });
                                });
                        };

                        Prompt({
                            hdr: 'Remove Label from ' + templateName,
                            body: '<div class="Prompt-bodyQuery">Confirm  the removal of the <span class="Prompt-emphasis">' + labelName + '</span> label.</div>',
                            action: action,
                            actionText: 'REMOVE'
                        });
                    };
                }
            };
        }
    ];
