/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default {
    name: 'activityStream',
    route: '/activity_stream?target&id',
    searchPrefix: 'activity',
    data: {
        activityStream: true
    },
    params: {
        activity_search: {
            value: {
                // default params will not generate search tags
                order_by: '-timestamp',
                or__object1: null,
                or__object2: null
            }
        }
    },
    ncyBreadcrumb: {
        label: "ACTIVITY STREAM"
    },
    onExit: function() {
        $('#stream-detail-modal').modal('hide');
        $('.modal-backdrop').remove();
        $('body').removeClass('modal-open');
    },
    views: {
        'list@': {
            controller: 'activityStreamController',
            templateProvider: function(StreamList, generateList) {
                let html = generateList.build({
                    list: StreamList,
                    mode: 'edit'
                });
                html = generateList.wrapPanel(html);
                return html;
            }
        }
    },
    resolve: {
        Dataset: ['StreamList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = GetBasePath(list.basePath) || GetBasePath(list.name);
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ],
        features: ['FeaturesService', 'ProcessErrors', '$state', '$rootScope',
            function(FeaturesService, ProcessErrors, $state, $rootScope) {
                var features = FeaturesService.get();
                if (features) {
                    if (FeaturesService.featureEnabled('activity_streams')) {
                        return features;
                    } else {
                        $state.go('dashboard');
                    }
                }
                $rootScope.featuresConfigured.promise.then(function(features) {
                    if (features) {
                        if (FeaturesService.featureEnabled('activity_streams')) {
                            return features;
                        } else {
                            $state.go('dashboard');
                        }
                    }
                });
            }
        ],
        subTitle: ['$stateParams',
            'Rest',
            'ModelToBasePathKey',
            'GetBasePath',
            'ProcessErrors',
            function($stateParams, rest, ModelToBasePathKey, getBasePath, ProcessErrors) {
                // If we have a target and an ID then we want to go grab the name of the object
                // that we're examining with the activity stream.  This name will be used in the
                // subtitle.
                if ($stateParams.target && $stateParams.id) {
                    var target = $stateParams.target;
                    var id = $stateParams.id;

                    var url = getBasePath(ModelToBasePathKey(target)) + id + '/';
                    rest.setUrl(url);
                    return rest.get()
                        .then(function(data) {
                            // Return the name or the username depending on which is available.
                            return (data.data.name || data.data.username);
                        }).catch(function(response) {
                            ProcessErrors(null, response.data, response.status, null, {
                                hdr: 'Error!',
                                msg: 'Failed to get title info. GET returned status: ' +
                                    response.status
                            });
                        });
                } else {
                    return null;
                }
            }
        ]
    }
};
