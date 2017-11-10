from awx.conf.license import (
    feature_enabled,
    LicenseForbids,
)


class ActivityStreamEnforcementMixin(object):
    '''
    Mixin to check that license supports activity streams.
    '''
    def check_permissions(self, request):
        if not feature_enabled('activity_streams'):
            raise LicenseForbids(_('Your license does not allow use of the activity stream.'))
        return super(ActivityStreamEnforcementMixin, self).check_permissions(request)
    

class WorkflowsEnforcementMixin(object):
    '''
    Mixin to check that license supports workflows.
    '''
    def check_permissions(self, request):
        if not feature_enabled('workflows') and request.method not in ('GET', 'OPTIONS', 'DELETE'):
            raise LicenseForbids(_('Your license does not allow use of workflows.'))
        return super(WorkflowsEnforcementMixin, self).check_permissions(request)


class EnforceParentRelationshipMixin(object):
    '''
    Useful when you have a self-refering ManyToManyRelationship.
    * Tower uses a shallow (2-deep only) url pattern. For example:

    When an object hangs off of a parent object you would have the url of the
    form /api/v1/parent_model/34/child_model. If you then wanted a child of the
    child model you would NOT do /api/v1/parent_model/34/child_model/87/child_child_model
    Instead, you would access the child_child_model via /api/v1/child_child_model/87/
    and you would create child_child_model's off of /api/v1/child_model/87/child_child_model_set
    Now, when creating child_child_model related to child_model you still want to
    link child_child_model to parent_model. That's what this class is for
    '''
    enforce_parent_relationship = ''

    def update_raw_data(self, data):
        data.pop(self.enforce_parent_relationship, None)
        return super(EnforceParentRelationshipMixin, self).update_raw_data(data)

    def create(self, request, *args, **kwargs):
        # Inject parent group inventory ID into new group data.
        data = request.data
        # HACK: Make request data mutable.
        if getattr(data, '_mutable', None) is False:
            data._mutable = True
        data[self.enforce_parent_relationship] = getattr(self.get_parent_object(), '%s_id' % self.enforce_parent_relationship)
        return super(EnforceParentRelationshipMixin, self).create(request, *args, **kwargs)


class UnifiedJobDeletionMixin(object):
    '''
    Special handling when deleting a running unified job object.
    '''
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'delete', obj):
            raise PermissionDenied()
        try:
            if obj.unified_job_node.workflow_job.status in ACTIVE_STATES:
                raise PermissionDenied(detail=_('Cannot delete job resource when associated workflow job is running.'))
        except self.model.unified_job_node.RelatedObjectDoesNotExist:
            pass
        if obj.status in ACTIVE_STATES:
            raise PermissionDenied(detail=_("Cannot delete running job resource."))
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
