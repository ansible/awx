/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$http', '$q', function($http, $q) {
    return {
        getInitialPageForList: function(id, url, pageSize) {
            // get the name of the object
            if ($.isNumeric(id)) {
                return $http.get(url + "?id=" + id)
                    .then(function (data) {
                        var queryValue, queryType;
                        if (data.data.results.length) {
                            if (data.data.results[0].type === "user") {
                                queryValue = data.data.results[0].username;
                                queryType = "username";
                            } else {
                                queryValue = data.data.results[0].name;
                                queryType = "name";
                            }
                        } else {
                            queryValue = "";
                            queryType = "name";
                        }
                        // get how many results are less than or equal to
                        // the name
                        return $http.get(url + "?" + queryType + "__lte=" + queryValue)
                            .then(function (data) {
                                // divide by the page size to get what
                                // page the data should be on
                                var count = data.data.count;
                                return Math.max(1, Math.ceil(count/parseInt(pageSize)));
                            });
                    });
            } else {
                var defer = $q.defer();
                defer.resolve(1);
                return(defer.promise);
            }
        }
    };
}];
