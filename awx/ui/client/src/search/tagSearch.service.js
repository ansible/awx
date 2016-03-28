export default ['Rest', '$q', 'GetBasePath', function(Rest, $q, GetBasePath) {
    var that = this;
    // parse the field config object to return
    // one of the searchTypes (for the left dropdown)
    this.buildType = function (field, key, id) {
        // build the value (key)
        var value;
        if (typeof(field.key) === String) {
            value = field.key;
        } else {
            value = key;
        }

        // build the label
        var label = field.searchLabel || field.label;

        // build the search type
        var type, typeOptions;
        if (field.searchType === 'select') {
            type = 'select';
            typeOptions = [];
        } else if (field.searchType === 'boolean') {
            type = 'select';
            typeOptions = [{label: "Yes", value: true},
                {label: "No", value: false}];
        } else {
            type = 'text';
        }

        // return the built option
        if (type === 'select') {
            return {
                id: id,
                value: value,
                label: label,
                type: type,
                typeOptions: typeOptions
            };
        } else {
            return {
                id: id,
                value: value,
                label: label,
                type: type
            };
        }
    };

    // given the fields that are searchable,
    // return searchTypes in the format the view can use
    this.getSearchTypes = function(list, basePath) {
        var defer = $q.defer();

        var options = Object
            .keys(list)
            .map(function(key, id) {
                return that.buildType(list[key], key, id);
        });

        var needsRequest, passThrough;

        // splits off options that need a request from
        // those that don't
        var partitionedOptions = _.partition(options, function(opt) {
            return (opt.typeOptions && !opt.typeOptions
                .length) ? true : false;
        });

        needsRequest = partitionedOptions[0];
        passThrough = partitionedOptions[1];

        var joinOptions = function() {
            return _.sortBy(_
                .flatten([needsRequest, passThrough]), function(opt) {
                    return opt.id;
                });
        };

        if (needsRequest.length) {
            // make the options request to reutrn the typeOptions
            Rest.setUrl(GetBasePath(basePath));
            Rest.options()
                .success(function (data) {
                    var options = data.actions.GET;
                    needsRequest = needsRequest
                        .map(function (option) {
                            option.typeOptions = options[option
                                .value]
                                    .choices
                                    .map(function(i) {
                                        return {
                                            value: i[0],
                                            label: i[1]
                                        };
                        });

                    return option;
                });

                defer.resolve(joinOptions());
            });
        } else {
            defer.resolve(joinOptions());
        }

        return defer.promise;
    };

    // returns the url with filter params
    this.updateFilteredUrl = function(basePath, tags, pageSize) {
        return GetBasePath(basePath) + "?" +
            (tags || []).map(function (t) {
                return t.url;
            }).join("&") + "&page_size=" + pageSize;
    };

    // given the field and input filters, create the tag object
    this.getTag = function(field, textVal, selectVal) {
        var tag = _.clone(field);
        if (tag.type === "text") {
            tag.url = tag.value + "__icontains=" + textVal;
            tag.name = textVal;
        } else {
            tag.url = tag.value + "=" + selectVal.value;
            tag.name = selectVal.label;
        }
        return tag;
    };

    // returns true if the newTag is already in the list of tags
    this.isDuplicate = function(tags, newTag) {
        return (tags
            .filter(function(tag) {
                return (tag.url === newTag.url);
            }).length > 0);
    };

    // returns an array of tags (or empty array if there are none)
    // .slice(0) is used so the currentTags variable is not directly mutated
    this.getCurrentTags = function(currentTags) {
      if (currentTags && currentTags.length) {
        return currentTags.slice(0);
      }
      return [];
    };

    return this;
}];
