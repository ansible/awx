/* eslint-disable react/jsx-no-useless-fragment */
import 'styled-components/macro';
import React, { useContext, useState, useEffect, useCallback } from 'react';
import { useHistory } from 'react-router-dom';
import { t } from '@lingui/macro';
import { Formik, useFormikContext } from 'formik';
import yaml from 'js-yaml';
import { bool, node, func } from 'prop-types';
import {
  Button,
  WizardContextConsumer,
  WizardFooter,
  Form,
} from '@patternfly/react-core';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';

import useRequest, { useDismissableError } from 'hooks/useRequest';
import mergeExtraVars from 'util/prompt/mergeExtraVars';
import getSurveyValues from 'util/prompt/getSurveyValues';
import { parseVariableField } from 'util/yaml';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from 'contexts/Workflow';
import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from 'api';
import Wizard from 'components/Wizard';
import AlertModal from 'components/AlertModal';
import useWorkflowNodeSteps from './useWorkflowNodeSteps';
import NodeNextButton from './NodeNextButton';

function NodeModalForm({
  askLinkType,
  onSave,
  title,
  credentialError,
  launchConfig,
  surveyConfig,
  isLaunchLoading,
  resourceDefaultCredentials,
}) {
  const history = useHistory();
  const dispatch = useContext(WorkflowDispatchContext);
  const { values, setFieldTouched } = useFormikContext();

  const [triggerNext, setTriggerNext] = useState(0);

  const clearQueryParams = () => {
    const parts = history.location.search.replace(/^\?/, '').split('&');
    const otherParts = parts.filter((param) =>
      /^!(job_templates\.|projects\.|inventory_sources\.|workflow_job_templates\.)/.test(
        param
      )
    );
    history.replace(`${history.location.pathname}?${otherParts.join('&')}`);
  };

  const {
    steps: promptSteps,
    validateStep,
    visitStep,
    visitAllSteps,
    contentError,
  } = useWorkflowNodeSteps(
    launchConfig,
    surveyConfig,
    values.nodeResource,
    askLinkType,
    resourceDefaultCredentials
  );

  const handleSaveNode = () => {
    clearQueryParams();
    if (values.nodeType !== 'workflow_approval_template') {
      delete values.approvalName;
      delete values.approvalDescription;
      delete values.timeoutMinutes;
      delete values.timeoutSeconds;
    }

    if (
      ['job_template', 'workflow_job_template'].includes(values.nodeType) &&
      (launchConfig.ask_variables_on_launch || launchConfig.survey_enabled)
    ) {
      let extraVars;
      const surveyValues = getSurveyValues(values);
      const initialExtraVars =
        launchConfig.ask_variables_on_launch && (values.extra_vars || '---');
      if (surveyConfig?.spec) {
        extraVars = yaml.dump(mergeExtraVars(initialExtraVars, surveyValues));
      } else {
        extraVars = yaml.dump(mergeExtraVars(initialExtraVars, {}));
      }
      values.extra_data = extraVars && parseVariableField(extraVars);
      delete values.extra_vars;
    } else if (
      values.nodeType === 'system_job_template' &&
      ['cleanup_activitystream', 'cleanup_jobs'].includes(
        values?.nodeResource?.job_type
      )
    ) {
      values.extra_data = {
        days: parseInt(values?.daysToKeep, 10),
      };
    }

    delete values.daysToKeep;
    onSave(values, launchConfig);
  };

  const handleCancel = () => {
    clearQueryParams();
    dispatch({ type: 'CANCEL_NODE_MODAL' });
  };

  const { error, dismissError } = useDismissableError(
    contentError || credentialError
  );

  function nextButtonText(activeStep) {
    let verifyPromptSteps = false;
    if (promptSteps.length) {
      verifyPromptSteps =
        activeStep.id === promptSteps[promptSteps.length - 1]?.id;
    }
    return verifyPromptSteps || activeStep.name === 'Preview'
      ? t`Save`
      : t`Next`;
  }

  const CustomFooter = (
    <WizardFooter>
      <WizardContextConsumer>
        {({ activeStep, onNext, onBack }) => (
          <>
            <NodeNextButton
              isDisabled={isLaunchLoading}
              triggerNext={triggerNext}
              activeStep={activeStep}
              aria-label={nextButtonText(activeStep)}
              onNext={onNext}
              onClick={() => setTriggerNext(triggerNext + 1)}
              buttonText={nextButtonText(activeStep)}
            />
            {activeStep && activeStep.id !== promptSteps[0]?.id && (
              <Button
                ouiaId="node-modal-back-button"
                id="back-node-modal"
                variant="secondary"
                aria-label={t`Back`}
                onClick={onBack}
              >
                {t`Back`}
              </Button>
            )}
            <Button
              ouiaId="node-modal-cancel-button"
              id="cancel-node-modal"
              variant="link"
              aria-label={t`Cancel`}
              onClick={handleCancel}
            >
              {t`Cancel`}
            </Button>
          </>
        )}
      </WizardContextConsumer>
    </WizardFooter>
  );

  if (error) {
    return (
      <AlertModal
        isOpen={error}
        variant="error"
        title={t`Error!`}
        onClose={() => {
          dismissError();
        }}
      >
        <ContentError error={error} />
      </AlertModal>
    );
  }

  if (error && !isLaunchLoading) {
    return (
      <AlertModal
        isOpen={error}
        variant="error"
        title={t`Error!`}
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
      isOpen={!error}
      onClose={handleCancel}
      onSave={() => {
        handleSaveNode();
      }}
      onBack={async (nextStep) => {
        validateStep(nextStep.id);
      }}
      onGoToStep={async (nextStep, prevStep) => {
        if (nextStep.id === 'preview') {
          visitAllSteps(setFieldTouched);
        } else {
          visitStep(prevStep.prevId, setFieldTouched);
          validateStep(nextStep.id);
        }
      }}
      steps={promptSteps}
      css="overflow: scroll"
      title={title}
      onNext={async (nextStep, prevStep) => {
        if (nextStep.id === 'preview') {
          visitAllSteps(setFieldTouched);
        } else {
          visitStep(prevStep.prevId, setFieldTouched);
          validateStep(nextStep.id);
        }
      }}
    />
  );
}

const NodeModalInner = ({ title, ...rest }) => {
  const { values } = useFormikContext();

  const wizardTitle = values.nodeResource
    ? `${title} | ${values.nodeResource.name}`
    : title;

  const {
    request: readLaunchConfigs,
    error: launchConfigError,
    result: { launchConfig, surveyConfig, resourceDefaultCredentials },
    isLoading,
  } = useRequest(
    useCallback(async () => {
      const readLaunch = (type, id) =>
        type === 'workflow_job_template'
          ? WorkflowJobTemplatesAPI.readLaunch(id)
          : JobTemplatesAPI.readLaunch(id);
      if (
        !values.nodeResource ||
        !['job_template', 'workflow_job_template'].includes(values?.nodeType) ||
        !['job_template', 'workflow_job_template'].includes(
          values.nodeResource?.type
        )
      ) {
        return {
          launchConfig: {},
          surveyConfig: {},
          resourceDefaultCredentials: [],
        };
      }

      const { data: launch } = await readLaunch(
        values.nodeType,
        values?.nodeResource?.id
      );

      let survey = {};

      if (launch.survey_enabled) {
        const { data } = launch?.workflow_job_template_data
          ? await WorkflowJobTemplatesAPI.readSurvey(
              launch?.workflow_job_template_data?.id
            )
          : await JobTemplatesAPI.readSurvey(launch?.job_template_data?.id);

        survey = data;
      }

      let defaultCredentials = [];

      if (launch.ask_credential_on_launch) {
        const {
          data: { results },
        } = await JobTemplatesAPI.readCredentials(values?.nodeResource?.id, {
          page_size: 200,
        });
        defaultCredentials = results;
      }

      return {
        launchConfig: launch,
        surveyConfig: survey,
        resourceDefaultCredentials: defaultCredentials,
      };

      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [values.nodeResource, values.nodeType]),
    {}
  );

  useEffect(() => {
    readLaunchConfigs();
  }, [readLaunchConfigs, values.nodeResource]);

  const { error, dismissError } = useDismissableError(launchConfigError);

  if (error) {
    return (
      <AlertModal
        isOpen={error}
        variant="error"
        title={t`Error!`}
        onClose={() => {
          dismissError();
        }}
      >
        <ContentError error={error} />
      </AlertModal>
    );
  }

  if (!launchConfig || !surveyConfig) {
    return (
      <Wizard
        isOpen
        steps={[
          {
            name: t`Loading`,
            component: <ContentLoading />,
          },
        ]}
        title={wizardTitle}
        footer={<></>}
      />
    );
  }

  return (
    <NodeModalForm
      {...rest}
      launchConfig={launchConfig}
      surveyConfig={surveyConfig}
      resourceDefaultCredentials={resourceDefaultCredentials}
      isLaunchLoading={isLoading}
      title={wizardTitle}
    />
  );
};

const NodeModal = ({ onSave, askLinkType, title }) => {
  const { nodeToEdit } = useContext(WorkflowStateContext);
  const onSaveForm = (values, config) => {
    onSave(values, config);
  };

  return (
    <Formik
      initialValues={{
        approvalName: '',
        approvalDescription: '',
        daysToKeep: 30,
        timeoutMinutes: 0,
        timeoutSeconds: 0,
        convergence: 'any',
        linkType: 'success',
        nodeResource: nodeToEdit?.fullUnifiedJobTemplate || null,
        nodeType: nodeToEdit?.fullUnifiedJobTemplate?.type || 'job_template',
      }}
      onSave={() => onSaveForm}
    >
      {(formik) => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <NodeModalInner
            onSave={onSaveForm}
            title={title}
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

export default NodeModal;
