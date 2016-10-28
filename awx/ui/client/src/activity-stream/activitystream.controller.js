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
function activityStreamController($scope, $state, subTitle, Stream, GetTargetTitle, list, Dataset) {

    init();

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

}

export default ['$scope', '$state', 'subTitle', 'Stream', 'GetTargetTitle', 'StreamList', 'Dataset', activityStreamController];
