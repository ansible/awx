import React, { useCallback, useEffect } from 'react';
import { t } from '@lingui/macro';
import useRequest from '../../../util/useRequest';
import {
  WorkflowJobTemplateNodesAPI,
  JobTemplatesAPI,
  WorkflowJobTemplatesAPI,
} from '../../../api';

import CredentialsStep from './CredentialsStep';

const STEP_ID = 'credentials';

export default function useCredentialsStep(
  config,
  i18n,
  selectedResource,
  nodeToEdit
) {
  const resource = nodeToEdit || selectedResource;
  const { request: fetchCredentials, result, error, isLoading } = useRequest(
    useCallback(async () => {
      let credentials;
      if (!nodeToEdit?.related?.credentials) {
        return {};
      }
      const {
        data: { results },
      } = await WorkflowJobTemplateNodesAPI.readCredentials(nodeToEdit.id);
      credentials = results;
      if (results.length === 0 && config?.defaults?.credentials) {
        const fetchCreds = config.job_template_data
          ? JobTemplatesAPI.readDetail(config.job_template_data.id)
          : WorkflowJobTemplatesAPI.readDetail(
              config.workflow_job_template_data.id
            );

        const {
          data: {
            summary_fields: { credentials: defaultCreds },
          },
        } = await fetchCreds;
        credentials = defaultCreds;
      }
      return credentials;
    }, [nodeToEdit, config])
  );
  useEffect(() => {
    fetchCredentials();
  }, [fetchCredentials, nodeToEdit]);

  const validate = () => {
    return {};
  };

  return {
    step: getStep(config, i18n),
    initialValues: getInitialValues(config, resource, result),
    validate,
    isReady: !isLoading && !!result,
    contentError: error,
    formError: null,
    setTouched: setFieldsTouched => {
      setFieldsTouched({
        credentials: true,
      });
    },
  };
}

function getStep(config, i18n) {
  if (!config.ask_credential_on_launch) {
    return null;
  }
  return {
    id: STEP_ID,
    key: 4,
    name: i18n._(t`Credentials`),
    component: <CredentialsStep i18n={i18n} />,
    enableNext: true,
  };
}

function getInitialValues(config, resource, result) {
  if (!config.ask_credential_on_launch) {
    return {};
  }
  return {
    credentials: resource?.summary_fields?.credentials || result || [],
  };
}
