import React, { useContext, useEffect, useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '@contexts/Workflow';

import { Button, Modal } from '@patternfly/react-core';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import PromptDetail from '@components/PromptDetail';
import useRequest from '@util/useRequest';
import {
  InventorySourcesAPI,
  JobTemplatesAPI,
  ProjectsAPI,
  WorkflowJobTemplatesAPI,
} from '@api';

function getNodeType(node) {
  const ujtType = node.type || node.unified_job_type;

  let nodeType;
  let nodeAPI;
  switch (ujtType) {
    case 'job_template':
    case 'job':
      nodeType = 'job_template';
      nodeAPI = JobTemplatesAPI;
      break;
    case 'project':
    case 'project_update':
      nodeType = 'project_sync';
      nodeAPI = ProjectsAPI;
      break;
    case 'inventory_source':
    case 'inventory_update':
      nodeType = 'inventory_source_sync';
      nodeAPI = InventorySourcesAPI;
      break;
    case 'workflow_job_template':
    case 'workflow_job':
      nodeType = 'workflow_job_template';
      nodeAPI = WorkflowJobTemplatesAPI;
      break;
    case 'workflow_approval_template':
    case 'workflow_approval':
      nodeType = 'approval';
      nodeAPI = null;
      break;
    default:
  }
  return [nodeType, nodeAPI];
}

function NodeViewModal({ i18n }) {
  const dispatch = useContext(WorkflowDispatchContext);
  const { nodeToView } = useContext(WorkflowStateContext);
  const { unifiedJobTemplate } = nodeToView;
  const [nodeType, nodeAPI] = getNodeType(unifiedJobTemplate);

  const {
    result: launchConfig,
    isLoading: isLaunchConfigLoading,
    error: launchConfigError,
    request: fetchLaunchConfig,
  } = useRequest(
    useCallback(async () => {
      const readLaunch =
        nodeType === 'workflow_job_template'
          ? WorkflowJobTemplatesAPI.readLaunch(unifiedJobTemplate.id)
          : JobTemplatesAPI.readLaunch(unifiedJobTemplate.id);
      const { data } = await readLaunch;
      return data;
    }, [nodeType, unifiedJobTemplate.id]),
    {}
  );

  const {
    result: nodeDetail,
    isLoading: isNodeDetailLoading,
    error: nodeDetailError,
    request: fetchNodeDetail,
  } = useRequest(
    useCallback(async () => {
      const { data } = await nodeAPI?.readDetail(unifiedJobTemplate.id);
      return data;
    }, [nodeAPI, unifiedJobTemplate.id]),
    null
  );

  useEffect(() => {
    if (nodeType === 'workflow_job_template' || nodeType === 'job_template') {
      fetchLaunchConfig();
    }

    if (unifiedJobTemplate.unified_job_type && nodeType !== 'approval') {
      fetchNodeDetail();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (nodeDetail) {
      dispatch({
        type: 'REFRESH_NODE',
        node: {
          nodeResource: nodeDetail,
        },
      });
    }
  }, [nodeDetail]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleEdit = () => {
    dispatch({ type: 'SET_NODE_TO_VIEW', value: null });
    dispatch({ type: 'SET_NODE_TO_EDIT', value: nodeToView });
  };

  let Content;
  if (isLaunchConfigLoading || isNodeDetailLoading) {
    Content = <ContentLoading />;
  } else if (launchConfigError || nodeDetailError) {
    Content = <ContentError error={launchConfigError || nodeDetailError} />;
  } else {
    Content = (
      <PromptDetail launchConfig={launchConfig} resource={unifiedJobTemplate} />
    );
  }

  return (
    <Modal
      isLarge
      isOpen
      isFooterLeftAligned
      title={unifiedJobTemplate.name}
      onClose={() => dispatch({ type: 'SET_NODE_TO_VIEW', value: null })}
      actions={[
        <Button
          key="edit"
          aria-label={i18n._(t`Edit Node`)}
          onClick={handleEdit}
        >
          {i18n._(t`Edit`)}
        </Button>,
      ]}
    >
      {Content}
    </Modal>
  );
}

export default withI18n()(NodeViewModal);
