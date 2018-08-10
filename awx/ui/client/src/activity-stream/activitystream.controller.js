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
export default ['$scope', '$state', 'subTitle', 'GetTargetTitle',
    'StreamList', 'Dataset', '$rootScope', 'ShowDetail', 'BuildDescription',
    function activityStreamController($scope, $state, subTitle, GetTargetTitle,
    list, Dataset, $rootScope, ShowDetail, BuildDescription) {

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

        $rootScope.flashMessage = null;

        $scope.refreshStream = function () {
            $state.go('.', null, {reload: true});
        };

        $scope.showDetail = function (id) {
            ShowDetail({
                scope: $scope,
                activity_id: id
            });
        };

        if($scope.activities && $scope.activities.length > 0) {
            buildUserAndDescription();
        }

        $scope.$watch('activities', function(){
            // Watch for future update to scope.activities (like page change, column sort, search, etc)
            buildUserAndDescription();
        });

        function buildUserAndDescription(){
            $scope.activities.forEach(function(activity, i) {
                // build activity.user
                if ($scope.activities[i].summary_fields.actor) {
                    if ($scope.activities[i].summary_fields.actor.id) {
                        $scope.activities[i].user = "<a href=\"/#/users/" + $scope.activities[i].summary_fields.actor.id  + "\">" +
                            $scope.activities[i].summary_fields.actor.username + "</a>";
                    } else {
                        $scope.activities[i].user = $scope.activities[i].summary_fields.actor.username + ' (deleted)';
                    }
                } else {
                    $scope.activities[i].user = 'system';
                }
                // build description column / action text
                BuildDescription($scope.activities[i]);

            });
        }
        
        const route = _.find($state.$current.path, (step) => {
            return step.params.hasOwnProperty('activity_search');
        });
        let defaultParams = angular.copy(route.params.activity_search.config.value);

        defaultParams.or__object1__in = $state.params.activity_search.or__object1__in ? $state.params.activity_search.or__object1__in : defaultParams.or__object1__in;
        defaultParams.or__object2__in = $state.params.activity_search.or__object2__in ? $state.params.activity_search.or__object2__in : defaultParams.or__object2__in;

        $scope[`${list.iterator}_default_params`] = defaultParams;
    }
];
