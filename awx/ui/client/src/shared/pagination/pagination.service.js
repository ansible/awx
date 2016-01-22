/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$http', function($http) {
    return {
        getInitialPageForList: function(id, url, pageSize) {
            // get the name of the object
            return $http.get(url + "?id=" + id)
                .then(function (data) {
                    var queryValue, queryType;
                    if (data.data.results[0].type === "user") {
                        queryValue = data.data.results[0].username;
                        queryType = "username";
                    } else {
                        queryValue = data.data.results[0].name;
                        queryType = "name";
                    }
                    // get how many results are less than or equal to
                    // the name
                    return $http.get(url + "?" + queryType + "__lte=" + queryValue)
                        .then(function (data) {
                            // divide by the page size to get what
                            // page the data should be on
                            var count = data.data.count;
                            return Math.ceil(count/pageSize);
                        });
                });
        }
    };
}];
