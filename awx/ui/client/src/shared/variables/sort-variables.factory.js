export default
    function SortVariables() {
        return function(variableObj) {
            var newObj;
            function sortIt(objToSort) {
                var i,
                    keys = Object.keys(objToSort),
                    newObj = {};
                keys = keys.sort();
                for (i=0; i < keys.length; i++) {
                    if (typeof objToSort[keys[i]] === 'object' && objToSort[keys[i]] !== null && !Array.isArray(objToSort[keys[i]])) {
                        newObj[keys[i]] = sortIt(objToSort[keys[i]]);
                    }
                    else {
                        newObj[keys[i]] = objToSort[keys[i]];
                    }
                }
                return newObj;
            }
            newObj = sortIt(variableObj);
            return newObj;
        };
    }
