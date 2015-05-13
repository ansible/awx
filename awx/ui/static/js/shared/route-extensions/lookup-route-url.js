export function lookupRouteUrl(name, routes, models) {
    var route = _.find(routes, {name: name});

    if (angular.isUndefined(route)) {
        throw "Unknown route " + name;
    }

    var routeUrl = route.originalPath;

    if (!angular.isUndefined(models) && angular.isObject(models)) {
        var match = routeUrl.match(route.regexp);
        var keyMatchers = match.slice(1);

        routeUrl =
            keyMatchers.reduce(function(url, keyMatcher) {
                var value;
                var key = keyMatcher.replace(/^:/, '');

                var model = models[key];

                if (angular.isArray(model)) {
                    value = _.compact(_.pluck(model, key));

                    if (_.isEmpty(value)) {
                        value = _.pluck(model, 'id');
                    }

                    value = value.join(',');
                } else if (angular.isObject(model)) {
                    value = model[key];

                    if (_.isEmpty(value)) {
                        value = model.id;
                    }
                }

                return url.replace(keyMatcher, value);
            }, routeUrl);

    }

    return routeUrl;
}
