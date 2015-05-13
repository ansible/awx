// Typically ng-include requires the use of an extra tag like:
//
//  <div ng-include="my-partial.html"></div>
//
// This means that the content from `my-partial.html` will _always_
// be wrapped in that extra div.
//
// This directive works with ngInclude to replace its own contents with
// the contents of the included partial.
//
// The high-level strategy here is to find the comment
// inserted by ng-include, remove all children after
// the comment (this will be the children inserted by
// this directiv) then insert the included children
// after the comment.
//
// So say we have:
//
// <include-partial ng-include="'my-partial.html'"></include-partial>
//
// and "my-partial.html" contains:
//
// <p>Item 1</p>
// <p>Item 2</p>
// <p>Item 3</p>
//
// When the <include-partial> link function runs the
// DOM will look like:
//
// <!-- ngInclude: 'my-partial.html' -->
// <include-partial ng-include="'my-partial.html'">
//     <p>Item 1</p>
//     <p>Item 2</p>
//     <p>Item 3</p>
// </include-partial>
//
// First we find the comment, then we get all the
// chilren of <include-partial> (the contents of 'my-partial.html').
//
// Then we remove the <include-partial> tag and
// insert the its contents after the comment.
//
// There is a potential bug here if the <include-partial>
// is followed by other siblings, they will get removed
// too. We can fix this probably by inserting another
// comment and removing everything between the two
// comments instead.

export default function() {
    return {
        restrict: 'E',
        link: function(scope, linkElement) {
            var contents = Array.prototype.slice.apply(linkElement.parent().contents());
            var commentNode = contents.filter(function(node) {
                // This selects a comment node
                return node.nodeType === 8;
            });

            var children = linkElement.children();
            $(commentNode[0]).nextAll().remove();
            $(commentNode[0]).after(children);
        }
    };
}
