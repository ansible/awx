export default
    function() {
        return function formatResults(compareKey, displayKey, results) {
            return results.reduce(function(arr, value) {
                var obj =
                    {   keyName: value[compareKey],
                        value1: value.position === 0 ? value[displayKey] : 'absent',
                        value2: value.position === 1 ? value[displayKey] : 'absent'
                };
                return arr.concat(obj);
            }, []);
        };
    }
