export default [function() {
    // given the list, return the fields that need searching
    this.getList = function(list) {
        return JSON.stringify(Object
            .keys(list.fields)
            .filter(function(i) {
                return (list.fields[i]
                    .searchable !== false);
            }).map(function(i) {
                return {[i]: list.fields[i]};
            }).reduce(function (acc, i) {
                var key = Object.keys(i);
                acc[key] = i[key];
                return acc;
            }));
    };

    // given the list config object, return the basepath
    this.getEndpoint = function(list) {
        return list.basePath || list.name;
    };

    // inject the directive with the list and endpoint
    this.inject = function(list, endpoint) {
        return "<tag-search list='" + list +
            "' endpoint='" + endpoint +
            "'></tag-search>";
    };

    return this;
}];
