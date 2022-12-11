from uuid import uuid4

from collections import OrderedDict

from rest_framework.response import Response
from rest_framework import status

from awx.api.generics import APIView
from rest_framework.permissions import IsAuthenticated
from awx.api import serializers

from awx.api.views import WorkflowJobList
from awx.main.models import WorkflowJob, WorkflowJobNode, UnifiedJobTemplate, Inventory, InventorySource, Credential


class BulkJobView(WorkflowJobList):
    def get_queryset(self):
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(workflow_job_template=None, is_bulk_job=True).distinct()


class BulkJobLaunchView(APIView):
    _ignore_model_permissions = True
    permission_classes = [IsAuthenticated]  # FIXME: Could finde/make a permissions class more tailored to this view

    def get(self, request):
        # FIXME: Could return something more sensible to a GET
        msg = "POST to this endpoint to launch an adhoc workflow"
        return Response(msg)

    def post(self, request):
        workflow_node_data = []
        launch_template_ids = {'project_id': [], 'inventory_source_id': [], 'job_template_id': [], 'workflow_job_template_id': []}
        inventory_ids = []
        credential_ids = []
        node_identifiers = []
        workflow_nodes = []
        node_m2m_objects = {}
        num_nodes = len(request.data.get('workflow_job_nodes', []))
        allowed_node_fields = WorkflowJobNode._get_workflow_job_field_names()
        allowed_node_fields.remove('workflow_job')
        allowed_node_fields.remove('unified_job_template')
        allowed_node_fields.append('identifier')

        # Creating the workflow nodes in the web request like this is a little risky, we have
        # to limit the number of nodes we are dealing with here to make sure we are snappy to respond
        # Also, the WorkflowManager has some vulnerability to workflows with very large numbers of workflow job nodes
        # so we can prevent problems by just providing some sane maximum
        if num_nodes == 0:
            return Response("AdHoc Workflows must contain at least one workflow job node in 'workflow_job_nodes' list.", status=status.HTTP_400_BAD_REQUEST)
        if num_nodes > 100:
            return Response(f"{num_nodes} exceeds maximum of 100 nodes in AdHoc Workflow", status=status.HTTP_400_BAD_REQUEST)

        node_errors = []

        # Build data for creating workflow nodes and do some sanity checking before we create any job or nodes
        for node in request.data['workflow_job_nodes']:
            node_relationship_keys = ['always_nodes', 'success_nodes', 'failure_nodes']
            if any([k in node.keys() for k in node_relationship_keys]):
                node_errors.append(f"{node_relationship_keys} not supported on adhoc workflow job nodes at this time.")
            kwargs = {key: node[key] for key in node.keys() if key in allowed_node_fields}

            this_launch_template_id = set(node.keys()).intersection(set(launch_template_ids.keys()))
            if this_launch_template_id:
                if len(set(this_launch_template_id)) > 1:
                    node_errors.append(f"only one of {launch_template_ids.keys()} allowed per workflow job node")

                this_launch_template_id = this_launch_template_id.pop()
                if isinstance(node[this_launch_template_id], int):
                    kwargs['unified_job_template'] = node[this_launch_template_id]
                    launch_template_ids[this_launch_template_id].append(node[this_launch_template_id])
                else:
                    node_errors.append(f"{this_launch_template_id} must be an integer id")
                    continue
            else:
                node_errors.append(f"One of {launch_template_ids.keys()} is a required to create a workflow_job_node")
                continue

            if 'identifier' not in kwargs:
                kwargs['identifier'] = uuid4()
            else:
                if kwargs['identifier'] in node_identifiers:
                    node_errors.append(f"node identifier {kwargs['identifier']} not unique")
                    continue
                node_identifiers.append(kwargs['identifier'])
            node_m2m_objects[kwargs['identifier']] = {}

            if 'inventory' in kwargs:
                if isinstance(node['inventory'], int):
                    inventory_ids.append(kwargs['inventory'])
                else:
                    node_errors.append("inventory must be an integer id of the inventory to use")
                    continue
            if 'credentials' in kwargs:
                if isinstance(kwargs['credentials'], list) and all([isinstance(item, int) for item in kwargs['credentials']]):
                    credential_ids.extend(kwargs['credentials'])
                else:
                    node_errors.append("credentials specified on a workflow_job_node must be a list of integer ids of the credentials to use")
                    continue

            workflow_node_data.append(kwargs)

        # Collect the objects needed to create the workflow nodes and ensure we have access
        # If we don't have access or non-existent objects are specified, return error before
        # creating the workflow job

        # FIXME: Inventory Source Updates not working yet!!!
        # JobTemplates have "execute_role", project updates have "use_role"...but InventorySources...I think you have to have
        # 'update_role' on the related Inventory...need to think about how to get that info
        all_launch_template_ids = {item for sublist in launch_template_ids.values() for item in sublist}

        # Find out all the ujts we have permission to launch
        if not request.user.is_superuser:
            accessible_ujts = set()
            if len(launch_template_ids['job_template_id']) > 0 or len(launch_template_ids['workflow_job_template_id']) > 0:
                accessible_ujts = accessible_ujts.union({item[0] for item in UnifiedJobTemplate.accessible_pk_qs(request.user, 'execute_role').all()})
            if len(launch_template_ids['project_id']) > 0 or len(launch_template_ids['inventory_source_id']) > 0:
                accessible_ujts = accessible_ujts.union({item[0] for item in UnifiedJobTemplate.accessible_pk_qs(request.user, 'update_role').all()})
            if len(launch_template_ids['inventory_source_id']) > 0:
                accessible_ujts = accessible_ujts.union(
                    {
                        item
                        for item in InventorySource.objects.filter(inventory__in=accessible_ujts)
                        .filter(id__in=all_launch_template_ids)
                        .values_list('id', flat=True)
                    }
                )
            accessible_ujts = all_launch_template_ids.intersection(accessible_ujts)
        else:
            accessible_ujts = all_launch_template_ids

        # Filter down to the ones we want to launch

        ujts = request.user.get_queryset(UnifiedJobTemplate).filter(id__in=accessible_ujts)
        ujt_map = {ujt.id: ujt for ujt in ujts}
        if all_launch_template_ids != set(ujt_map.keys()):
            node_errors.append(f"Unable to locate or lack permissions to unified_job_templates: {all_launch_template_ids - set(ujt_map.keys())}")

        if len(inventory_ids) > 0:
            inventory_ids = set(inventory_ids)
            if not request.user.is_superuser:
                accessible_inventory_ids = inventory_ids.intersection({item[0] for item in Inventory.accessible_pk_qs(request.user, 'read_role').all()})
            else:
                accessible_inventory_ids = inventory_ids
            invs = request.user.get_queryset(Inventory).filter(id__in=accessible_inventory_ids)
            inv_map = {inv.id: inv for inv in invs}
            if inventory_ids != set(inv_map.keys()):
                node_errors.append(f"Unable to locate or lack permissions to inventory objects: {set(inventory_ids) - set(inv_map.keys())}")
        if len(credential_ids) > 0:
            credential_ids = set(credential_ids)
            if not request.user.is_superuser:
                accessible_credential_ids = credential_ids.intersection({item[0] for item in Credential.accessible_pk_qs(request.user, 'read_role').all()})
            else:
                accessible_credential_ids = credential_ids
            creds = request.user.get_queryset(Credential).filter(id__in=accessible_credential_ids)
            cred_map = {cred.id: cred for cred in creds}
            if credential_ids != set(cred_map.keys()):
                node_errors.append(f"Unable to locate or lack permissions to credentials: {set(credential_ids) - set(cred_map.keys())}")

        if len(node_errors) > 0:
            return Response(' '.join(node_errors), status=status.HTTP_400_BAD_REQUEST)

        # Now that we have validated the workflow job node input and acess to underlying resources,
        # we can create the workflow job and the workflow nodes
        name = request.data['name'] if 'name' in request.data else 'AdHocWorkflow'
        wfj = WorkflowJob.objects.create(name=name, is_bulk_job=True)
        for kwargs in workflow_node_data:
            kwargs['unified_job_template'] = ujt_map[kwargs['unified_job_template']]
            if 'inventory' in kwargs:
                kwargs['inventory'] = inv_map[kwargs['inventory']]
            if 'credentials' in kwargs:
                # Have to set m2m fields like credentials after node is created
                creds = [cred_map[cred_id] for cred_id in kwargs['credentials']]
                node_m2m_objects[kwargs['identifier']]['credentials'] = creds
                kwargs.pop('credentials')
            wf_node = WorkflowJobNode(workflow_job=wfj, created=wfj.created, modified=wfj.modified, **kwargs)
            workflow_nodes.append(wf_node)

        try:
            workflow_nodes = WorkflowJobNode.objects.bulk_create(workflow_nodes)
            CredThroughModel = WorkflowJobNode.credentials.through
            cred_through_models = []
            for node in workflow_nodes:
                if 'credentials' in node_m2m_objects[node.identifier]:
                    for cred in node_m2m_objects[node.identifier]['credentials']:
                        cred_through_models.append(CredThroughModel(credential=cred, workflowjobnode=node))
            CredThroughModel.objects.bulk_create(cred_through_models)
            # Now that nodes are created, we can move the workflowjob from 'new' to 'pending' so the task manager
            # will pick it up and spawn the jobs
            wfj.status = 'pending'
            wfj.save()
        except Exception as e:
            # Something went wrong, have the job end in error
            wfj.status = 'error'
            wfj.job_explanation = 'Error encounted at launch, aborted adhoc workflow job'
            wfj.save()
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        data = OrderedDict()
        data['workflow_job'] = wfj.id
        data.update(serializers.WorkflowJobSerializer(wfj).to_representation(wfj))
        headers = {'Location': wfj.get_absolute_url(request)}
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)
