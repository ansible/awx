export default ['Rest', '$q', 'GetBasePath', 'Wait', 'ProcessErrors', '$log', function(Rest, $q, GetBasePath, Wait, ProcessErrors, $log) {
    var that = this;
    // parse the field config object to return
    // one of the searchTypes (for the left dropdown)
    this.buildType = function (field, key, id) {
        var obj = {};
        // build the value (key)
        var value;
        if (field.sourceModel && field.sourceField) {
            value = field.sourceModel + '__' + field.sourceField;
            obj.related = true;
        } else if (typeof(field.key) === String) {
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
            typeOptions = field.searchOptions || [];
        } else if (field.searchType === 'boolean') {
            type = 'select';
            typeOptions = [{label: "Yes", value: true},
                {label: "No", value: false}];
        } else {
            type = 'text';
        }

        obj.id = id;
        obj.value = value;
        obj.label = label;
        obj.type = type;
        obj.basePath = field.basePath || null;

        // return the built option
        if (type === 'select') {
            obj.typeOptions = typeOptions;
        }

        return obj;
    };

    // given the fields that are searchable,
    // return searchTypes in the format the view can use
    this.getSearchTypes = function(list, basePath) {
        Wait("start");
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
            Rest.setUrl(needsRequest[0].basePath ? GetBasePath(needsRequest[0].basePath) : basePath);
            Rest.options()
                .success(function (data) {
                    try {
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
                    }
                    catch(err){
                        if (!basePath){
                            $log.error('Cannot retrieve OPTIONS because the basePath parameter is not set on the list with the following fieldset: \n', list);
                        }
                        else { $log.error(err); }
                    }
                    Wait("stop");
                    defer.resolve(joinOptions());
                })
                .error(function (data, status) {
                    Wait("stop");
                    defer.reject("options request failed");
                    ProcessErrors(null, data, status, null, {
                        hdr: 'Error!',
                        msg: 'Getting type options failed'});
                });
        } else {
            Wait("stop");
            defer.resolve(joinOptions());
        }

        return defer.promise;
    };

    // returns the url with filter params
    this.updateFilteredUrl = function(basePath, tags, pageSize) {
        // remove the chain directive from all the urls that might have
        // been added previously
        tags = (tags || []).map(function(val) {
            if (val.url.indexOf("chain__") !== -1) {
                val.url = val.url.substring(("chain__").length);
            }
            return val;
        });

        // separate those tags with the related: true attribute
        var separateRelated = _.partition(tags, function(i) {
            return i.related;
        });

        var relatedTags = separateRelated[0];
        var nonRelatedTags = separateRelated[1];

        if (relatedTags.length > 1) {
            // separate query params that need the change directive
            // but have different keys
            var chainGroups = _.groupBy(relatedTags, function(i) {
                return i.value;
            });

            // iterate over those groups and add the "chain__" to the
            // beginning of all but the first of each url
            relatedTags = _.flatten(_.map(chainGroups, function(group) {
                return group.map(function(val, i) {
                    if (i !== 0) {
                        val.url = "chain__" + val.url;
                    }
                    return val;
                });
            }));

            // combine the related and non related tags after chainifying
            tags = relatedTags.concat(nonRelatedTags);
        }

        return basePath + "?" +
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
