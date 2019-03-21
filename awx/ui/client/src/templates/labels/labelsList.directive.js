/* jshint unused: vars */
export default
    [   'templateUrl',
        'Wait',
        'Rest',
        'GetBasePath',
        'ProcessErrors',
        'Prompt',
        '$q',
        '$filter',
        '$state',
        'i18n',
        function(templateUrl, Wait, Rest, GetBasePath, ProcessErrors, Prompt, $q, $filter, $state, i18n) {
            return {
                restrict: 'E',
                scope: {
                    state: '='
                },
                templateUrl: templateUrl('templates/labels/labelsList'),
                link: function(scope, element, attrs) {
                    scope.showDelete = attrs.showDelete === 'true';
                    scope.isRowItem = attrs.isRowItem === 'true';
                    scope.seeMoreInactive = true;

                    var getNext = function(data, arr, resolve) {
                        Rest.setUrl(data.next);
                        Rest.get()
                            .then(({data}) => {
                                if (data.next) {
                                    getNext(data, arr.concat(data.results), resolve);
                                } else {
                                    resolve.resolve(arr.concat(data.results));
                                }
                            });
                    };

                    scope.seeMore = function () {
                        var seeMoreResolve = $q.defer();
                        if (scope.state) {
                            Rest.setUrl(scope.state.related.labels);
                        }
                        Rest.get()
                            .then(({data}) => {
                                if (data.next) {
                                    getNext(data, data.results, seeMoreResolve);
                                } else {
                                    seeMoreResolve.resolve(data.results);
                                }
                            });

                        seeMoreResolve.promise.then(function (labels) {
                            scope.labels = labels;
                            scope.seeMoreInactive = false;
                        });
                    };

                    scope.seeLess = function() {
                        // Trim the labels array back down to 10 items
                        scope.labels = scope.labels.slice(0, 5);
                        // Re-set the seeMoreInteractive flag so that the "See More" will be displayed
                        scope.seeMoreInactive = true;
                    };

                    scope.deleteLabel = function(template, label) {
                        var action = function () {
                            $('#prompt-modal').modal('hide');
                            scope.seeMoreInactive = true;
                            Wait('start');
                            let url;
                            if(template.type === 'job_template') {
                                url = GetBasePath("job_templates") + template.id + "/labels/";
                            }
                            else if(template.type === 'workflow_job_template') {
                                url = GetBasePath("workflow_job_templates") + template.id + "/labels/";
                            }

                            if(url) {
                                Rest.setUrl(url);
                                Rest.post({"disassociate": true, "id": label.id})
                                    .then(() => {
                                        Wait('stop');
                                        $state.go('.', null, {reload: true});
                                    })
                                    .catch(({data, status}) => {
                                        Wait('stop');
                                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                            msg: 'Could not disassociate label from JT.  Call to ' + url + ' failed. DELETE returned status: ' + status });
                                    });
                            }
                        };

                        Prompt({
                            hdr: i18n._('Remove Label from ') + template.name,
                            body: '<div class="Prompt-bodyQuery">Confirm  the removal of the <span class="Prompt-emphasis">' + $filter('sanitize')(label.name) + '</span> label.</div>',
                            action: action,
                            actionText: i18n._('REMOVE')
                        });
                    };

                    if (_.has(scope.state, 'summary_fields.labels.results')) {
                        scope.labels = scope.state.summary_fields.labels.results.slice(0, 5);
                        scope.count = scope.state.summary_fields.labels.count;
                       } else {
                        scope.$watchCollection(scope.state, function() {
                            // To keep the array of labels fresh, we need to set up a watcher - otherwise, the
                            // array will get set initially and then never be updated as labels are removed
                            if (scope.state.summary_fields.labels){
                                scope.labels = scope.state.summary_fields.labels.results.slice(0, 5);
                                scope.count = scope.state.summary_fields.labels.count;
                            }
                            else{
                                scope.labels = null;
                                scope.count = null;
                            }
                        });
                    }

                }
            };
        }
    ];
