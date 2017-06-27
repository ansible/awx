export default
    function NextPage(Rest, $q) {
        return function(params) {

            let getNext = function(getNextParams){
                Rest.setUrl(getNextParams.url);
                return Rest.get()
                    .then(function (res) {
                        if (res.data.next) {
                            return getNext({
                                url: res.data.next,
                                arrayOfValues: getNextParams.arrayOfValues.concat(res.data.results)
                            });
                        } else {
                            return $q.resolve(getNextParams.arrayOfValues.concat(res.data.results));
                        }
                    })
                    .catch(function(response) {
                        return $q.reject( response );
                    });
            };

            return getNext(params);

        };
    }

NextPage.$inject = ['Rest', '$q'];
