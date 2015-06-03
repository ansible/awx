/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

function lodashAsPromised($q) {

    var lodash = _.runInContext();
    var _aw = {};
    var toExtend =
        [   'map',
            'filter',
            'reduce',
            'pluck',
            'compact',
            'xor',
            'groupBy',
            'thru'
        ];

    function log(label, obj) {
        /* jshint ignore:start */
        console.log(label, obj);
        /* jshint ignore:end */
        return obj;
    }

    function _reject(value, reason) {
        return $q.reject(reason);
    }

    function _promise(value) {
        return $q.when(value);
    }

    function _then(promise, fn) {
        return promise.then(function(value) {
            if (_.isFunction(value.then)) {
                return _then(value, fn);
            } else {
                return fn(value);
            }
       });
    }

    function _catch(promise, fn) {
        return promise.catch(fn);
    }

    function _finally(promise, fn) {
        return promise.finally(fn);
    }

 function thenAll(arr, then, deep) {
    var doAll = function (arr) {
      var promise = $q.all(arr).then(function (resolvedArr) {
        if (deep) {
          return lodash(resolvedArr)
            .thenMap(function (elem) {
              if (_.isArray(elem)) {
                return thenAll(elem, null, true);
              } else {
                return elem;
              }
            })
            .thenAll()
            .value();
        } else {
          return resolvedArr;
        }
      });
      return then ? promise.then(then) : promise;
    };
    if (arr.then) {
      return arr.then(doAll);
    } else {
      return doAll(arr);
    }
  }

  function thenFlatten(array, isShallow, callback, thisArg) {
      return thenAll(array, _.partialRight(_.flatten, isShallow, callback, thisArg), true);
  }

    function wrapCallback(method, callback, thisArg, collection) {
        return method(collection, function(value, index, collection) {
            if (_.isUndefined(value)) {
                return callback(value, index, collection);
            } else if (_.isFunction(value.then)) {
                return value.then(_.partialRight(callback, index, collection));
            } else {
                return callback(value, index, collection);
            }
        }, thisArg);
    }

    function promiseWrapper(method, collection, callback, thisArg) {
        if (_.isFunction(collection.then)) {
            return collection.then(
                _.partial(wrapCallback, method, callback, thisArg));
        } else {
            return $q.all(collection)
                .then(function(unwrappedResults) {
                    return method(unwrappedResults, callback, thisArg);
                });
        }
    }

    toExtend.forEach(function(fnName) {
        var wrappedName = 'then' + _.capitalize(fnName);
        _aw[wrappedName] = _.partial(promiseWrapper, _[fnName]);
    });

    _aw.promise = _promise;
    _aw.reject = _reject;
    _aw.then = _then;
    _aw.catch = _catch;
    _aw.finally = _finally;
    _aw.thenAll = thenAll;
    _aw.thenFlatten = thenFlatten;
    _aw.log = log;

    lodash.mixin(_aw);

    return lodash;
}

export default ['$q', lodashAsPromised];
