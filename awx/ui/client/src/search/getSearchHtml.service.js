export default ['GetBasePath', function(GetBasePath) {
    // given the list, return the fields that need searching
    this.getList = function(list) {
        var f = _.cloneDeep(list.fields);
        return JSON.stringify(Object
            .keys(f)
            .filter(function(i) {
                return (f[i]
                    .searchable !== false);
            }).map(function(i) {
                // delete any fields which might include AngularJS interpolation tags {{ }}
                delete f[i].awToolTip;
                delete f[i].awPopover;
                delete f[i].linkTo;
                delete f[i].dataTitle;
                delete f[i].ngClass;
                delete f[i].ngClick;
                delete f[i].icon;
                delete f[i].linkTo;
                return {[i]: f[i]};
            }).reduce(function (acc, i) {
                var key = Object.keys(i);
                acc[key] = i[key];
                return acc;
            }));
    };

    // given the list config object, return the basepath
    this.getEndpoint = function(list) {
        var endPoint = (list.basePath || list.name);
        if (endPoint === 'inventories') {
            endPoint = 'inventory';
        }
        return GetBasePath(endPoint);
    };

    // inject the directive with the list and endpoint
    this.inject = function(list, endpoint, set, iterator) {
        return "<tag-search list='" + list +
            "' endpoint='" + endpoint +
            "' set='" + set +
            "' iterator='" + iterator + "'></tag-search>";
    };

    return this;
}];
