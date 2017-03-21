/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Activity Stream
 * @description This controller controls the activity stream.
 */
export default ['$scope', '$state', 'subTitle', 'Stream', 'GetTargetTitle',
    'StreamList', 'Dataset',
    function activityStreamController($scope, $state, subTitle, Stream,
    GetTargetTitle, list, Dataset) {

        init();
        initOmitSmartTags();

        function init() {
            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

            // subTitle is passed in via a resolve on the route.  If there is no subtitle
            // generated in the resolve then we go get the targets generic title.

            // Get the streams sub-title based on the target.  This scope variable is leveraged
            // when we define the activity stream list.  Specifically it is included in the list
            // title.
            $scope.streamSubTitle = subTitle ? subTitle : GetTargetTitle($state.params.target);

            // Open the stream
            Stream({
                scope: $scope
            });
        }

        // Specification of smart-tags omission from the UI is done in the route/state init.
        // A limitation is that this specficiation is static and the key for which to be omitted from
        // the smart-tags must be known at that time.
        // In the case of activity stream, we won't to dynamically ommit the resource for which we are
        // displaying the activity stream for. i.e. 'project', 'credential', etc.
        function initOmitSmartTags() {
            let defaults, route = _.find($state.$current.path, (step) => {
                return step.params.hasOwnProperty('activity_search');
            });
            if (route && $state.params.target !== undefined) {
                defaults = route.params.activity_search.config.value;
                defaults[$state.params.target] = null;
            }
        }
    }
];
