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
                scope: false,
                templateUrl: templateUrl('inventories-hosts/inventories/related/hosts/related-groups-labels/relatedGroupsLabelsList'),
                link: function(scope, element, attrs) {
                    scope.showDelete = attrs.showDelete === 'true';
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
                        Rest.setUrl(`${scope[scope.$parent.list.iterator].related.groups}?order_by=id`);
                        Rest.get()
                            .then(({data}) => {
                                if (data.next) {
                                    getNext(data, data.results, seeMoreResolve);
                                } else {
                                    seeMoreResolve.resolve(data.results);
                                }
                            });

                        seeMoreResolve.promise.then(function (groups) {
                            scope.related_groups = groups;
                            scope.seeMoreInactive = false;
                        });
                    };

                    scope.seeLess = function() {
                        // Trim the groups array back down to 5 items
                        scope.related_groups = scope.related_groups.slice(0, 5);
                        // Re-set the seeMoreInteractive flag so that the "See More" will be displayed
                        scope.seeMoreInactive = true;
                    };

                    scope.deleteLabel = function(host, group) {
                        var action = function () {
                            $('#prompt-modal').modal('hide');
                            scope.seeMoreInactive = true;
                            Wait('start');
                            let url = `${GetBasePath('groups')}${group.id}/hosts`;
                            if(url) {
                                Rest.setUrl(url);
                                Rest.post({"disassociate": true, "id": host.id})
                                    .then(() => {
                                        Wait('stop');
                                        $state.go('.', null, {reload: true});
                                    })
                                    .catch(({data, status}) => {
                                        Wait('stop');
                                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                            msg: 'Could not disassociate host from group.  Call to ' + url + ' failed. DELETE returned status: ' + status });
                                    });
                            }
                        };

                        Prompt({
                            hdr: i18n._('Remove host from ') + group.name ,
                            body: '<div class="Prompt-bodyQuery">' + i18n._('Confirm the removal of the') + ' <span class="Prompt-emphasis">' + $filter('sanitize')(host.name) + '</span> ' + i18n._('from the') + ' <span class="Prompt-emphasis">' + $filter('sanitize')(group.name) + '</span> ' + i18n._('group') + '.</div>',
                            action: action,
                            actionText: i18n._('REMOVE')
                        });
                    };

                    scope.$watchCollection(scope.$parent.list.iterator, function() {
                        // To keep the array of groups fresh, we need to set up a watcher - otherwise, the
                        // array will get set initially and then never be updated as groups are removed
                        if (scope[scope.$parent.list.iterator].summary_fields.groups){
                            scope.related_groups = scope[scope.$parent.list.iterator].summary_fields.groups.results;
                            scope.count = scope[scope.$parent.list.iterator].summary_fields.groups.count;
                        }
                        else{
                            scope.related_groups = null;
                            scope.count = null;
                        }
                    });

                }
            };
        }
    ];
