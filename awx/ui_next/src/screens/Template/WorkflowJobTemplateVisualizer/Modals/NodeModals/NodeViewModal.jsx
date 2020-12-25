import React, { useContext, useEffect, useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button, Modal } from '@patternfly/react-core';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../../../contexts/Workflow';

import ContentError from '../../../../../components/ContentError';
import ContentLoading from '../../../../../components/ContentLoading';
import PromptDetail from '../../../../../components/PromptDetail';
import useRequest from '../../../../../util/useRequest';
import { jsonToYaml } from '../../../../../util/yaml';
import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from '../../../../../api';
import getNodeType from '../../shared/WorkflowJobTemplateVisualizerUtils';

function NodeViewModal({ i18n, readOnly }) {
  const dispatch = useContext(WorkflowDispatchContext);
  const { nodeToView } = useContext(WorkflowStateContext);
  const {
    fullUnifiedJobTemplate,
    originalNodeCredentials,
    originalNodeObject,
    promptValues,
  } = nodeToView;
  const [nodeType, nodeAPI] = getNodeType(
    fullUnifiedJobTemplate ||
      originalNodeObject?.summary_fields?.unified_job_template
  );

  const id =
    fullUnifiedJobTemplate?.id ||
    originalNodeObject?.summary_fields?.unified_job_template.id;

  const {
    result: launchConfig,
    isLoading: isLaunchConfigLoading,
    error: launchConfigError,
    request: fetchLaunchConfig,
  } = useRequest(
    useCallback(async () => {
      const readLaunch =
        nodeType === 'workflow_job_template'
          ? WorkflowJobTemplatesAPI.readLaunch(id)
          : JobTemplatesAPI.readLaunch(id);
      const { data } = await readLaunch;
      return data;
    }, [nodeType, id]),
    {}
  );

  const {
    result: relatedData,
    isLoading: isRelatedDataLoading,
    error: relatedDataError,
    request: fetchRelatedData,
  } = useRequest(
    useCallback(async () => {
      const related = {};
      if (
        nodeType === 'job_template' &&
        !fullUnifiedJobTemplate.instance_groups
      ) {
        const {
          data: { results = [] },
        } = await JobTemplatesAPI.readInstanceGroups(fullUnifiedJobTemplate.id);
        related.instance_groups = results;
      }

      if (
        fullUnifiedJobTemplate?.related?.webhook_receiver &&
        !fullUnifiedJobTemplate.webhook_key
      ) {
        const {
          data: { webhook_key },
        } = await nodeAPI?.readWebhookKey(fullUnifiedJobTemplate.id);
        related.webhook_key = webhook_key;
      }

      return related;
    }, [nodeAPI, fullUnifiedJobTemplate, nodeType]),
    null
  );

  useEffect(() => {
    if (nodeType === 'workflow_job_template' || nodeType === 'job_template') {
      fetchLaunchConfig();
    }

    if (
      fullUnifiedJobTemplate &&
      ((nodeType === 'job_template' &&
        !fullUnifiedJobTemplate.instance_groups) ||
        (fullUnifiedJobTemplate?.related?.webhook_receiver &&
          !fullUnifiedJobTemplate.webhook_key))
    ) {
      fetchRelatedData();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (relatedData) {
      dispatch({
        type: 'REFRESH_NODE',
        node: {
          fullUnifiedJobTemplate: { ...fullUnifiedJobTemplate, ...relatedData },
        },
      });
    }
  }, [relatedData]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleEdit = () => {
    dispatch({ type: 'SET_NODE_TO_VIEW', value: null });
    dispatch({ type: 'SET_NODE_TO_EDIT', value: nodeToView });
  };

  let Content;
  if (isLaunchConfigLoading || isRelatedDataLoading) {
    Content = <ContentLoading />;
  } else if (launchConfigError || relatedDataError) {
    Content = <ContentError error={launchConfigError || relatedDataError} />;
  } else if (!fullUnifiedJobTemplate) {
    Content = (
      <p>
        {i18n._(t`The resource associated with this node has been deleted.`)}
        &nbsp;&nbsp;
        {!readOnly
          ? i18n._(t`Click the Edit button below to reconfigure the node.`)
          : ''}
      </p>
    );
  } else {
    let overrides = {};

    if (promptValues) {
      overrides = promptValues;

      if (launchConfig.ask_variables_on_launch || launchConfig.survey_enabled) {
        overrides.extra_vars = jsonToYaml(
          JSON.stringify(promptValues.extra_data)
        );
      }
    } else if (
      fullUnifiedJobTemplate.id === originalNodeObject?.unified_job_template
    ) {
      if (launchConfig.ask_inventory_on_launch) {
        overrides.inventory = originalNodeObject.summary_fields.inventory;
      }
      if (launchConfig.ask_scm_branch_on_launch) {
        overrides.scm_branch = originalNodeObject.scm_branch;
      }
      if (launchConfig.ask_variables_on_launch || launchConfig.survey_enabled) {
        overrides.extra_vars = jsonToYaml(
          JSON.stringify(originalNodeObject.extra_data)
        );
      }
      if (launchConfig.ask_tags_on_launch) {
        overrides.job_tags = originalNodeObject.job_tags;
      }
      if (launchConfig.ask_diff_mode_on_launch) {
        overrides.diff_mode = originalNodeObject.diff_mode;
      }
      if (launchConfig.ask_skip_tags_on_launch) {
        overrides.skip_tags = originalNodeObject.skip_tags;
      }
      if (launchConfig.ask_job_type_on_launch) {
        overrides.job_type = originalNodeObject.job_type;
      }
      if (launchConfig.ask_limit_on_launch) {
        overrides.limit = originalNodeObject.limit;
      }
      if (launchConfig.ask_verbosity_on_launch) {
        overrides.verbosity = originalNodeObject.verbosity.toString();
      }
      if (launchConfig.ask_credential_on_launch) {
        overrides.credentials = originalNodeCredentials || [];
      }
    }

    Content = (
      <PromptDetail
        launchConfig={launchConfig}
        resource={fullUnifiedJobTemplate}
        overrides={overrides}
      />
    );
  }

  return (
    <Modal
      variant="large"
      isOpen
      title={fullUnifiedJobTemplate?.name || i18n._(t`Resource deleted`)}
      aria-label={i18n._(t`Workflow node view modal`)}
      onClose={() => dispatch({ type: 'SET_NODE_TO_VIEW', value: null })}
      actions={
        readOnly
          ? []
          : [
              <Button
                id="node-view-edit-button"
                key="edit"
                aria-label={i18n._(t`Edit Node`)}
                onClick={handleEdit}
              >
                {i18n._(t`Edit`)}
              </Button>,
            ]
      }
    >
      {Content}
    </Modal>
  );
}

export default withI18n()(NodeViewModal);
