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
import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from '@api';

function NodeViewModal({ i18n }) {
  const dispatch = useContext(WorkflowDispatchContext);
  const { nodeToView } = useContext(WorkflowStateContext);
  const { unifiedJobTemplate } = nodeToView;
  const jobType =
    unifiedJobTemplate.unified_job_type || unifiedJobTemplate.type;

  const {
    result: launchConfig,
    isLoading,
    error,
    request: fetchLaunchConfig,
  } = useRequest(
    useCallback(async () => {
      const readLaunch = ['workflow_job', 'workflow_job_template'].includes(
        jobType
      )
        ? WorkflowJobTemplatesAPI.readLaunch(unifiedJobTemplate.id)
        : JobTemplatesAPI.readLaunch(unifiedJobTemplate.id);

      const { data } = await readLaunch;

      return data;
    }, [jobType, unifiedJobTemplate]),
    {}
  );

  useEffect(() => {
    if (
      ['workflow_job', 'workflow_job_template', 'job', 'job_template'].includes(
        jobType
      )
    ) {
      fetchLaunchConfig();
    }
  }, [jobType, fetchLaunchConfig]);

  const handleEdit = () => {
    dispatch({ type: 'SET_NODE_TO_VIEW', value: null });
    dispatch({ type: 'SET_NODE_TO_EDIT', value: nodeToView });
  };

  let Content;

  if (isLoading) {
    Content = <ContentLoading />;
  } else if (error) {
    Content = <ContentError error={error} />;
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
