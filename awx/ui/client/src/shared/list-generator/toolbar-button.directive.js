/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['SelectIcon', function(SelectIcon) {
    return {
        restrict: 'A',
        scope: {},
        link: function(scope, element, attrs) {

            var toolbar = attrs.toolbar;

            if (toolbar) {
                //if this is a toolbar button, set some defaults
                attrs.class = 'btn-xs btn-primary';
                attrs.iconSize = 'fa-lg';
            }

            element.addClass('btn');

            // If no class specified, default
            // to btn-sm
            if (_.isEmpty(attrs.class)) {
                element.addClass("btn-sm");
            } else {
                element.addClass(attrs.class);
            }

            if (attrs.awPopOver) {
                element.addClass("help-link-white");
            }

            if (attrs.iconName && _.isEmpty(attrs.id)) {
                element.attr("id",attrs.iconName + "_btn");
            }

            if (!_.isEmpty(attrs.img)) {
                $("<img>")
                    .attr("src", $basePath + "assets/" + attrs.img)
                    .css({ width: "12px", height: "12px" })
                    .appendTo(element);
            }

            if (!_.isEmpty(attrs.iconClass)) {
                $("<i>")
                    .addClass(attrs.iconClass)
                    .appendTo(element);
            }
            else {
                var icon = SelectIcon({
                    action: attrs.iconName,
                    size: attrs.iconSize
                });

                $(icon).appendTo(element);
            }

            if (!toolbar && !_.isEmpty(attrs.label)) {
                element.text(attrs.label);
            }

        }
    };
}];
