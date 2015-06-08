/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export function formatFacts(diffedResults) {

    var loggingEnabled = false;

    function log(msg, obj) {
        if (loggingEnabled) {
            /* jshint ignore:start */
            console.log(msg, obj);
            /* jshint ignore:end */
        }
        return obj;
    }

    function isFlatFactArray(fact) {
        // Flat arrays will have the index as their
        // keyName
        return !_.isNaN(Number(fact.keyName));
    }

    function isNestedFactArray(fact) {
        // Nested arrays will have the index as the last element
        // in the keypath
        return !_.isNaN(Number(_.last(fact.keyPath)));
    }
    function isFactArray(fact) {
        return isNestedFactArray(fact) || isFlatFactArray(fact);
    }

        // Explode flat results into groups based matching
        // parent keypaths
        var grouped = _.groupBy(diffedResults, function(obj) {
            var leftKeyPathStr = obj.keyPath.join('.');
            log('obj.keyPath', obj.keyPath);
            return log('    reduced key', _.reduce(diffedResults, function(result, obj2) {
                log('        obj2.keyPath', obj2.keyPath);
                var rightKeyPathStr = obj2.keyPath.join('.');
                if (isFactArray(obj)) {
                    log('            number hit!', Number(_.last(obj.keyPath)));
                    return obj.keyPath.slice(0,-1);
                } else if (rightKeyPathStr && leftKeyPathStr !== rightKeyPathStr && log('        intersection', _.intersection(obj.keyPath, obj2.keyPath).join('.')) === rightKeyPathStr) {
                    log('            hit!');
                    return obj2.keyPath;
                } else {
                    log('            else hit!');
                    return result;
                }
            }, obj.keyPath)).join('.');
        });

        var normalized = _.mapValues(grouped, function(arr, rootKey) {
            log('processing', rootKey);
            var nestingLevel = 0;
            var trailingLength;
            return _(arr).sortBy('keyPath.length').tap(function(arr) {
                // Initialize trailing length to the shortest keyPath length
                // in the array (first item because we know it's sorted now)
                trailingLength = arr[0].keyPath.length;
            }).map(function(obj) {
                var keyPathStr = obj.keyPath.join('.');
                log('    calculating displayKeyPath for', keyPathStr);
                var rootKeyPath = rootKey.split('.');
                var displayKeyPath;
                // var factArrayIndex;
                var isFactArrayProp = isFactArray(obj);

                if (obj.keyPath.length > trailingLength) {
                    nestingLevel++;
                    trailingLength = obj.keyPath.length;
                }

                if (isNestedFactArray(obj)) {
                    // factArrayIndex = obj.keyPath.length > 1 ? Number(_.last(obj.keyPath)) : obj.keyName;
                    displayKeyPath = _.initial(obj.keyPath).join('.');
                } else if (keyPathStr !== rootKey) {
                    displayKeyPath = _.difference(obj.keyPath, rootKeyPath).join('.');
                } else {
                    displayKeyPath = rootKeyPath.join('.');
                }


                obj.displayKeyPath = displayKeyPath;
                obj.nestingLevel = nestingLevel;
                // obj.arrayPosition = factArrayIndex;
                obj.isArrayMember = isFactArrayProp;
                return obj;
            }).value();
        });

        var flattened = _.reduce(normalized, function(flat, value) {

            var groupedValues = _.groupBy(value, 'displayKeyPath');

            var groupArr =
                _.reduce(groupedValues, function(groupArr, facts, key) {
                    var isArray = facts[0].isArrayMember;
                    var nestingLevel = facts[0].nestingLevel;

                    if (isArray) {
                        facts = _(facts)
                                    .groupBy('arrayPosition')
                                    .values()
                                    .value();
                    }

                    var displayObj =
                        {   keyPath: key.split('.'),
                            displayKeyPath: key,
                            isNestedDisplay: true,
                            facts: facts,
                            isFactArray: isArray,
                            nestingLevel: nestingLevel
                        };
                    return groupArr.concat(displayObj);
                }, []);

            return flat.concat(groupArr);

        }, []);

        return flattened;
}

export function findFacts(factData) {
    var rightData = factData[0].facts;
    var leftData = factData[1].facts;

    function factObject(keyPath, key, leftValue, rightValue) {
        var obj =
            {   keyPath: keyPath,
                keyName: key,
                value1: leftValue,
                value2: rightValue
            };
        return obj;
    }

    function descend(parentValue, parentKey, parentKeys) {
        if (_.isObject(parentValue)) {
            return _.reduce(parentValue, function(all, value, key) {
                var merged = descend(value, key, parentKeys.concat(key));
                return all.concat(merged);
            }, []);
        } else {

            var rightValue =
                _.get(rightData,
                      parentKeys,
                      'absent');

            return factObject(
                // TODO: Currently parentKeys is getting passed with the final key
                // as the last element. Figure out how to have it passed
                // in correctly, so that it's all the keys leading up to
                // the value, but not the value's key itself
                // In the meantime, slicing the last element off the array
                parentKeys.slice(0,-1),
                parentKey,
                parentValue,
                rightValue);
        }
    }

    return _.reduce(leftData, function(mergedFacts, parentValue, parentKey) {

        var merged = descend(parentValue, parentKey, [parentKey]);

        return _.flatten(mergedFacts.concat(merged));

    }, []);
}
