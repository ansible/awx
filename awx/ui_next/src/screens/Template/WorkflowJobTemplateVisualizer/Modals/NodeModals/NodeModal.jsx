import 'styled-components/macro';
import React, { useContext, useState, useEffect, useCallback } from 'react';
import { useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Formik, useFormikContext } from 'formik';

import { bool, node, func } from 'prop-types';
import {
  Button,
  WizardContextConsumer,
  WizardFooter,
  Form,
} from '@patternfly/react-core';
import ContentError from '../../../../../components/ContentError';
import ContentLoading from '../../../../../components/ContentLoading';

import useRequest, {
  useDismissableError,
} from '../../../../../util/useRequest';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../../../contexts/Workflow';
import {
  JobTemplatesAPI,
  WorkflowJobTemplatesAPI,
  WorkflowJobTemplateNodesAPI,
} from '../../../../../api';
import Wizard from '../../../../../components/Wizard';
import useWorkflowNodeSteps from './useWorkflowNodeSteps';
import AlertModal from '../../../../../components/AlertModal';

import NodeNextButton from './NodeNextButton';

function canLaunchWithoutPrompt(nodeType, launchData) {
  if (nodeType !== 'workflow_job_template' && nodeType !== 'job_template') {
    return true;
  }
  return (
    launchData.can_start_without_user_input &&
    !launchData.ask_inventory_on_launch &&
    !launchData.ask_variables_on_launch &&
    !launchData.ask_limit_on_launch &&
    !launchData.ask_scm_branch_on_launch &&
    !launchData.survey_enabled &&
    (!launchData.variables_needed_to_start ||
      launchData.variables_needed_to_start.length === 0)
  );
}

function NodeModalForm({ askLinkType, i18n, onSave, title, credentialError }) {
  const history = useHistory();
  const dispatch = useContext(WorkflowDispatchContext);
  const { nodeToEdit } = useContext(WorkflowStateContext);
  const {
    values,
    setTouched,
    validateForm,
    setFieldValue,
    resetForm,
  } = useFormikContext();

  const [triggerNext, setTriggerNext] = useState(0);

  const clearQueryParams = () => {
    const parts = history.location.search.replace(/^\?/, '').split('&');
    const otherParts = parts.filter(param =>
      /^!(job_templates\.|projects\.|inventory_sources\.|workflow_job_templates\.)/.test(
        param
      )
    );
    history.replace(`${history.location.pathname}?${otherParts.join('&')}`);
  };
  useEffect(() => {
    if (values?.nodeResource?.summary_fields?.credentials?.length > 0) {
      setFieldValue(
        'credentials',
        values.nodeResource.summary_fields.credentials
      );
    }
    if (nodeToEdit?.unified_job_type === 'workflow_job') {
      setFieldValue('nodeType', 'workflow_job_template');
    }
    if (nodeToEdit?.unified_job_type === 'job') {
      setFieldValue('nodeType', 'job_template');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodeToEdit, values.nodeResource]);

  const {
    request: readLaunchConfig,
    error: launchConfigError,
    result: launchConfig,
    isLoading,
  } = useRequest(
    useCallback(async () => {
      const readLaunch = (type, id) =>
        type === 'workflow_job_template'
          ? WorkflowJobTemplatesAPI.readLaunch(id)
          : JobTemplatesAPI.readLaunch(id);
      if (
        (values?.nodeType === 'workflow_job_template' &&
          values.nodeResource?.unified_job_type === 'job') ||
        (values?.nodeType === 'job_template' &&
          values.nodeResource?.unified_job_type === 'workflow_job')
      ) {
        return {};
      }
      if (
        values.nodeType === 'workflow_job_template' ||
        values.nodeType === 'job_template'
      ) {
        if (values.nodeResource) {
          const { data } = await readLaunch(
            values.nodeType,
            values?.nodeResource?.id
          );

          return data;
        }
      }
      return {};
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [values.nodeResource, values.nodeType]),
    {}
  );

  useEffect(() => {
    readLaunchConfig();
  }, [readLaunchConfig, values.nodeResource, values.nodeType]);

  const {
    steps: promptSteps,
    initialValues,
    isReady,
    visitStep,
    visitAllSteps,
    contentError,
  } = useWorkflowNodeSteps(
    launchConfig,
    i18n,
    values.nodeResource,
    askLinkType,
    !canLaunchWithoutPrompt(values.nodeType, launchConfig)
  );

  const handleSaveNode = () => {
    clearQueryParams();
    onSave(values, askLinkType ? values.linkType : null, launchConfig);
  };

  const handleCancel = () => {
    clearQueryParams();
    dispatch({ type: 'CANCEL_NODE_MODAL' });
  };

  const { error, dismissError } = useDismissableError(
    launchConfigError || contentError || credentialError
  );
  useEffect(() => {
    if (isReady) {
      resetForm({
        values: {
          ...initialValues,
          nodeResource: values.nodeResource,
          nodeType: values.nodeType || 'job_template',
          linkType: values.linkType || 'success',
          verbosity: initialValues?.verbosity?.toString(),
        },
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [launchConfig, values.nodeType, isReady, values.nodeResource]);
  const steps = [...(isReady ? [...promptSteps] : [])];

  const CustomFooter = (
    <WizardFooter>
      <WizardContextConsumer>
        {({ activeStep, onNext, onBack }) => (
          <>
            <NodeNextButton
              triggerNext={triggerNext}
              activeStep={activeStep}
              onNext={onNext}
              onClick={() => setTriggerNext(triggerNext + 1)}
              buttonText={
                activeStep.id === steps[steps?.length - 1]?.id ||
                activeStep.name === 'Preview'
                  ? i18n._(t`Save`)
                  : i18n._(t`Next`)
              }
            />
            {activeStep && activeStep.id !== steps[0]?.id && (
              <Button id="back-node-modal" variant="secondary" onClick={onBack}>
                {i18n._(t`Back`)}
              </Button>
            )}
            <Button
              id="cancel-node-modal"
              variant="link"
              onClick={handleCancel}
            >
              {i18n._(t`Cancel`)}
            </Button>
          </>
        )}
      </WizardContextConsumer>
    </WizardFooter>
  );

  const wizardTitle = values.nodeResource
    ? `${title} | ${values.nodeResource.name}`
    : title;

  if (error && !isLoading) {
    return (
      <AlertModal
        isOpen={error}
        variant="error"
        title={i18n._(t`Error!`)}
        onClose={() => {
          dismissError();
        }}
      >
        <ContentError error={error} />
      </AlertModal>
    );
  }
  return (
    <Wizard
      footer={CustomFooter}
      isOpen={!error || !contentError}
      onClose={handleCancel}
      onSave={() => {
        handleSaveNode();
      }}
      onGoToStep={async (nextStep, prevStep) => {
        if (nextStep.id === 'preview') {
          visitAllSteps(setTouched);
        } else {
          visitStep(prevStep.prevId);
        }
        await validateForm();
      }}
      steps={
        isReady
          ? steps
          : [
              {
                name: i18n._(t`Content Loading`),
                component: <ContentLoading />,
              },
            ]
      }
      css="overflow: scroll"
      title={wizardTitle}
      onNext={async (nextStep, prevStep) => {
        if (nextStep.id === 'preview') {
          visitAllSteps(setTouched);
        } else {
          visitStep(prevStep.prevId);
        }
        await validateForm();
      }}
    />
  );
}

const NodeModal = ({ onSave, i18n, askLinkType, title }) => {
  const { nodeToEdit } = useContext(WorkflowStateContext);
  const onSaveForm = (values, linkType, config) => {
    onSave(values, linkType, config);
  };
  const { request: fetchCredentials, result, error } = useRequest(
    useCallback(async () => {
      const {
        data: { results },
      } = await WorkflowJobTemplateNodesAPI.readCredentials(
        nodeToEdit.originalNodeObject.id
      );
      return results;
    }, [nodeToEdit])
  );
  useEffect(() => {
    if (nodeToEdit?.originalNodeObject?.related?.credentials) {
      fetchCredentials();
    }
  }, [fetchCredentials, nodeToEdit]);

  return (
    <Formik
      initialValues={{
        linkType: 'success',
        nodeResource:
          nodeToEdit?.originalNodeObject?.summary_fields
            ?.unified_job_template || null,
        inventory:
          nodeToEdit?.originalNodeObject?.summary_fields?.inventory || null,
        credentials: result || null,
        verbosity: nodeToEdit?.originalNodeObject?.verbosity || 0,
        diff_mode: nodeToEdit?.originalNodeObject?.verbosty,
        skip_tags: nodeToEdit?.originalNodeObject?.skip_tags || '',
        job_tags: nodeToEdit?.originalNodeObject?.job_tags || '',
        scm_branch:
          nodeToEdit?.originalNodeObject?.scm_branch !== null
            ? nodeToEdit?.originalNodeObject?.scm_branch
            : '',
        job_type: nodeToEdit?.originalNodeObject?.job_type || 'run',
        extra_vars: nodeToEdit?.originalNodeObject?.extra_vars || '---',
      }}
      onSave={() => onSaveForm}
    >
      {formik => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <NodeModalForm
            onSave={onSaveForm}
            i18n={i18n}
            title={title}
            credentialError={error}
            askLinkType={askLinkType}
          />
        </Form>
      )}
    </Formik>
  );
};

NodeModal.propTypes = {
  askLinkType: bool.isRequired,
  onSave: func.isRequired,
  title: node.isRequired,
};

export default withI18n()(NodeModal);
