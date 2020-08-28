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
import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from '../../../../../api';
import Wizard from '../../../../../components/Wizard';
import useSteps from '../../../../../components/LaunchPrompt/useSteps';
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

function NodeModalForm({ askLinkType, i18n, onSave, title }) {
  const history = useHistory();
  const dispatch = useContext(WorkflowDispatchContext);
  const { nodeToEdit } = useContext(WorkflowStateContext);
  const {
    values,
    resetForm,
    setTouched,
    validateForm,
    setFieldValue,
  } = useFormikContext();

  // let defaultApprovalDescription = '';
  // let defaultApprovalName = '';
  // let defaultApprovalTimeout = 0;
  // let defaultNodeResource = null;
  // let defaultNodeType = 'job_template';
  // if (nodeToEdit && nodeToEdit.unifiedJobTemplate) {
  //   if (
  //     nodeToEdit &&
  //     nodeToEdit.unifiedJobTemplate &&
  //     (nodeToEdit.unifiedJobTemplate.type ||
  //       nodeToEdit.unifiedJobTemplate.unified_job_type)
  //   ) {
  //     const ujtType =
  //       nodeToEdit.unifiedJobTemplate.type ||
  //       nodeToEdit.unifiedJobTemplate.unified_job_type;
  //     switch (ujtType) {
  //       case 'job_template':
  //       case 'job':
  //         defaultNodeType = 'job_template';
  //         defaultNodeResource = nodeToEdit.unifiedJobTemplate;
  //         break;
  //       case 'project':
  //       case 'project_update':
  //         defaultNodeType = 'project_sync';
  //         defaultNodeResource = nodeToEdit.unifiedJobTemplate;
  //         break;
  //       case 'inventory_source':
  //       case 'inventory_update':
  //         defaultNodeType = 'inventory_source_sync';
  //         defaultNodeResource = nodeToEdit.unifiedJobTemplate;
  //         break;
  //       case 'workflow_job_template':
  //       case 'workflow_job':
  //         defaultNodeType = 'workflow_job_template';
  //         defaultNodeResource = nodeToEdit.unifiedJobTemplate;
  //         break;
  //       case 'workflow_approval_template':
  //       case 'workflow_approval':
  //         defaultNodeType = 'approval';
  //         defaultApprovalName = nodeToEdit.unifiedJobTemplate.name;
  //         defaultApprovalDescription =
  //           nodeToEdit.unifiedJobTemplate.description;
  //         defaultApprovalTimeout = nodeToEdit.unifiedJobTemplate.timeout;
  //         break;
  //       default:
  //     }
  //   }
  // }

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
    if (nodeToEdit?.unified_job_type === 'workflow_job') {
      setFieldValue('nodeType', 'workflow_job_template');
    }
    if (nodeToEdit?.unified_job_type === 'job') {
      setFieldValue('nodeType', 'job_template');
    }
  }, [nodeToEdit]);

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
    }, [values.nodeResource, values.nodeType]),
    {}
  );

  useEffect(() => {
    readLaunchConfig();
  }, [readLaunchConfig, values.nodeResource, values.nodeType]);

  const {
    steps: promptSteps,
    initialValues: promptStepsInitialValues,
    isReady,
    visitStep,
    visitAllSteps,
    contentError,
  } = useSteps(
    launchConfig,
    nodeToEdit,
    i18n,
    !canLaunchWithoutPrompt(values.nodeType, launchConfig),
    askLinkType,
    true,
    values.nodeResource
  );

  const handleSaveNode = () => {
    clearQueryParams();
    // nodeToEdit id, original node object,  unified job template,

    // const resource =
    //   values.nodeType === 'approval'
    //     ? {
    //         description: values.approvalDescription,
    //         name: values.approvalName,
    //         timeout: values.approvalTimeout,
    //         type: 'workflow_approval_template',
    //       }
    //     : values.nodeResource;
    // const editedNode = { id: 1, unified_job_template: { type: 'approval' } };
    console.log(values, 'values');
    onSave(launchConfig, values, askLinkType ? values.linkType : null);
  };

  const handleCancel = () => {
    clearQueryParams();
    dispatch({ type: 'CANCEL_NODE_MODAL' });
  };

  const { error, dismissError } = useDismissableError(
    launchConfigError || contentError
  );

  useEffect(() => {
    if (Object.values(promptStepsInitialValues).length > 0 && isReady) {
      resetForm({
        values: {
          ...promptStepsInitialValues,
          nodeResource:
            values.nodeResource || promptStepsInitialValues.nodeResource,
          nodeType:
            values.nodeType ||
            promptStepsInitialValues.nodeType ||
            'job_template',
          linkType: 'success',
          verbosity: promptStepsInitialValues?.verbosity?.toString(),
        },
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [launchConfig, values.nodeType, isReady]);
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
            {activeStep && activeStep.id !== 'runType' && (
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
      steps={
        isReady
          ? steps
          : [{ name: ContentLoading, component: <ContentLoading /> }]
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
  const onSaveForm = (resource, linkType, values) => {
    onSave(resource, linkType, values);
  };
  return (
    <Formik initialValues={{}} onSave={() => onSaveForm}>
      {formik => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <NodeModalForm
            onSave={onSaveForm}
            i18n={i18n}
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

export default withI18n()(NodeModal);
