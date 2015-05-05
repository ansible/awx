export default
    function() {
        return function xorObjects(key, thing1, thing2) {
            var values1 = _.pluck(thing1, key);
            var values2 = _.pluck(thing2, key);

            var valuesDiff = _.xor(values1, values2);

            return valuesDiff.reduce(function(arr, value) {
                var searcher = {};
                searcher[key] = value;

                var valuePosition1 = _.find(thing1, searcher);

                if (valuePosition1) {
                    valuePosition1.position = 0;
                }

                var valuePosition2 = _.find(thing2, searcher);

                if (valuePosition2) {
                    valuePosition2.position = 1;
                }

                return _.compact(arr.concat(valuePosition1).concat(valuePosition2));
            }, []);
        };
    }
