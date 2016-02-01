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
function activityStreamController($scope, Stream) {

    // Open the stream
    Stream({
        scope: $scope
    });
    
}

export default ['$scope', 'Stream', activityStreamController];
