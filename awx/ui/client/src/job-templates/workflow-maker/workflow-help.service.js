export default ['CreateDialog', 'Wait', '$q', '$state', function(CreateDialog, Wait, $q, $state){
    return {
        closeDialog: function() {
            $('#workflow-modal-dialog').dialog('destroy');

            $state.go('^');
        },
        searchTree: function(params) {
            // params.element
            // params.matchingId

            if(params.element.id === params.matchingId){
                 return params.element;
            }else if (params.element.children && params.element.children.length > 0){
                 let result = null;
                 const thisService = this;
                 _.forEach(params.element.children, function(child) {
                     result = thisService.searchTree({
                         element: child,
                         matchingId: params.matchingId
                     });
                     if(result) {
                         return false;
                     }
                 });
                 return result;
            }
            return null;
        },
        removeNodeFromTree: function(params) {
            // params.tree
            // params.nodeToBeDeleted

            let parentNode = this.searchTree({
                element: params.tree,
                matchingId: params.nodeToBeDeleted.parent.id
            });
            let nodeToBeDeleted = this.searchTree({
                element: parentNode,
                matchingId: params.nodeToBeDeleted.id
            });

            if(nodeToBeDeleted.children) {
                _.forEach(nodeToBeDeleted.children, function(child) {
                    if(nodeToBeDeleted.isRoot) {
                        child.isRoot = true;
                        child.edgeType = "always";
                    }

                    parentNode.children.push(child);
                });
            }

            _.forEach(parentNode.children, function(child, index) {
                if(child.id === params.nodeToBeDeleted.id) {
                    parentNode.children.splice(index, 1);
                    return false;
                }
            });
        },
        addPlaceholderNode: function(params) {
            // params.parent
            // params.betweenTwoNodes
            // params.tree
            // params.id

            let placeholder = {
                children: [],
                c: "#D7D7D7",
                id: params.id,
                canDelete: true,
                canEdit: false,
                canAddTo: true,
                placeholder: true,
                isNew: true,
                edited: false
            };

            let parentNode = (params.betweenTwoNodes) ? this.searchTree({element: params.tree, matchingId: params.parent.source.id}) : this.searchTree({element: params.tree, matchingId: params.parent.id});
            let placeholderRef;

            if(params.betweenTwoNodes) {
                _.forEach(parentNode.children, function(child, index) {
                    if(child.id === params.parent.target.id) {
                        placeholder.children.push(angular.copy(child));
                        parentNode.children[index] = placeholder;
                        placeholderRef = parentNode.children[index];
                        return false;
                    }
                });
            }
            else {
                if(parentNode.children) {
                    parentNode.children.push(placeholder);
                    placeholderRef = parentNode.children[parentNode.children.length - 1];
                } else {
                    parentNode.children = [placeholder];
                    placeholderRef = parentNode.children[0];
                }
            }

            return placeholderRef;
        },
        getSiblingConnectionTypes: function(params) {
            // params.parentId
            // params.tree

            let siblingConnectionTypes = {};

            let parentNode = this.searchTree({
                element: params.tree,
                matchingId: params.parentId
            });

            if(parentNode.children && parentNode.children.length > 0) {
                // Loop across them and add the types as keys to siblingConnectionTypes
                _.forEach(parentNode.children, function(child) {
                    if(!child.placeholder && child.edgeType) {
                        siblingConnectionTypes[child.edgeType] = true;
                    }
                });
            }

            return Object.keys(siblingConnectionTypes);
        }
    };
}];
