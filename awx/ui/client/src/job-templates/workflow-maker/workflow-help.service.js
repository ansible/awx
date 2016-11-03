export default ['CreateDialog', 'Wait', '$q', function(CreateDialog, Wait, $q){
    return {
        openDialog: function(params){
            // params.scope

            // let deferred = $q.defer();

            // if (params.scope.removeWorkflowDialogReady) {
            //     params.scope.removeWorkflowDialogReady();
            // }
            // params.scope.removeWorkflowDialogReady = params.scope.$on('WorkflowDialogReady', function() {
            //     $('#workflow-modal-dialog').dialog('open');

            //     deferred.resolve();
            // });
            // Wait('start');
            // debugger;
            // CreateDialog({
            //     id: 'workflow-modal-dialog',
            //     scope: params.scope,
            //     width: 1400,
            //     height: 720,
            //     draggable: false,
            //     dialogClass: 'SurveyMaker-dialog',
            //     position: ['center',20],
            //     onClose: function() {
            //         $('#workflow-modal-dialog').empty();
            //     },
            //     onOpen: function() {
            //         Wait('stop');

            //         // Let the modal height be variable based on the content
            //         // and set a uniform padding
            //         $('#workflow-modal-dialog').css({'padding': '20px'});

            //     },
            //     _allowInteraction: function(e) {
            //         return !!$(e.target).is('.select2-input') || this._super(e);
            //     },
            //     callback: 'WorkflowDialogReady'
            // });

            // return deferred.promise;
        },
        closeDialog: function() {
            $('#workflow-modal-dialog').dialog('destroy');
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
