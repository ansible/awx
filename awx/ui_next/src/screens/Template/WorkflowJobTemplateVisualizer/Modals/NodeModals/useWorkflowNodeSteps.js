import { useContext, useState, useEffect } from 'react';
import { useFormikContext } from 'formik';
import { t } from '@lingui/macro';
import useInventoryStep from '../../../../../components/LaunchPrompt/steps/useInventoryStep';
import useCredentialsStep from '../../../../../components/LaunchPrompt/steps/useCredentialsStep';
import useOtherPromptsStep from '../../../../../components/LaunchPrompt/steps/useOtherPromptsStep';
import useSurveyStep from '../../../../../components/LaunchPrompt/steps/useSurveyStep';
import usePreviewStep from '../../../../../components/LaunchPrompt/steps/usePreviewStep';
import { WorkflowStateContext } from '../../../../../contexts/Workflow';
import { jsonToYaml } from '../../../../../util/yaml';
import useNodeTypeStep from './NodeTypeStep/useNodeTypeStep';
import useRunTypeStep from './useRunTypeStep';

function showPreviewStep(nodeType, launchConfig) {
  if (
    !['workflow_job_template', 'job_template'].includes(nodeType) ||
    Object.keys(launchConfig).length === 0
  ) {
    return false;
  }
  return (
    !launchConfig.can_start_without_user_input ||
    launchConfig.ask_inventory_on_launch ||
    launchConfig.ask_variables_on_launch ||
    launchConfig.ask_limit_on_launch ||
    launchConfig.ask_scm_branch_on_launch ||
    launchConfig.survey_enabled ||
    (launchConfig.variables_needed_to_start &&
      launchConfig.variables_needed_to_start.length > 0)
  );
}

const getNodeToEditDefaultValues = (
  launchConfig,
  surveyConfig,
  nodeToEdit,
  resourceDefaultCredentials
) => {
  const initialValues = {
    nodeResource: nodeToEdit?.fullUnifiedJobTemplate || null,
    nodeType: nodeToEdit?.fullUnifiedJobTemplate?.type || 'job_template',
  };

  if (
    nodeToEdit?.fullUnifiedJobTemplate?.type === 'workflow_approval_template'
  ) {
    const timeout = nodeToEdit.fullUnifiedJobTemplate.timeout || 0;
    initialValues.approvalName = nodeToEdit.fullUnifiedJobTemplate.name || '';
    initialValues.approvalDescription =
      nodeToEdit.fullUnifiedJobTemplate.description || '';
    initialValues.timeoutMinutes = Math.floor(timeout / 60);
    initialValues.timeoutSeconds = timeout - Math.floor(timeout / 60) * 60;

    return initialValues;
  }

  if (!launchConfig || launchConfig === {}) {
    return initialValues;
  }

  if (launchConfig.ask_inventory_on_launch) {
    // We also need to handle the case where the UJT has been deleted.
    if (nodeToEdit?.promptValues) {
      initialValues.inventory = nodeToEdit?.promptValues?.inventory;
    } else if (nodeToEdit?.originalNodeObject?.summary_fields?.inventory) {
      initialValues.inventory =
        nodeToEdit?.originalNodeObject?.summary_fields?.inventory;
    } else {
      initialValues.inventory = null;
    }
  }

  if (launchConfig.ask_credential_on_launch) {
    if (nodeToEdit?.promptValues?.credentials) {
      initialValues.credentials = nodeToEdit?.promptValues?.credentials;
    } else if (nodeToEdit?.originalNodeCredentials) {
      const defaultCredsWithoutOverrides = [];

      const credentialHasOverride = templateDefaultCred => {
        let hasOverride = false;
        nodeToEdit.originalNodeCredentials.forEach(nodeCredential => {
          if (
            templateDefaultCred.credential_type ===
            nodeCredential.credential_type
          ) {
            if (
              (!templateDefaultCred.vault_id &&
                !nodeCredential.inputs.vault_id) ||
              (templateDefaultCred.vault_id &&
                nodeCredential.inputs.vault_id &&
                templateDefaultCred.vault_id === nodeCredential.inputs.vault_id)
            ) {
              hasOverride = true;
            }
          }
        });

        return hasOverride;
      };

      if (resourceDefaultCredentials) {
        resourceDefaultCredentials.forEach(defaultCred => {
          if (!credentialHasOverride(defaultCred)) {
            defaultCredsWithoutOverrides.push(defaultCred);
          }
        });
      }

      initialValues.credentials = nodeToEdit.originalNodeCredentials.concat(
        defaultCredsWithoutOverrides
      );
    } else {
      initialValues.credentials = [];
    }
  }

  const sourceOfValues =
    nodeToEdit?.promptValues || nodeToEdit.originalNodeObject;

  if (launchConfig.ask_job_type_on_launch) {
    initialValues.job_type = sourceOfValues?.job_type || '';
  }
  if (launchConfig.ask_limit_on_launch) {
    initialValues.limit = sourceOfValues?.limit || '';
  }
  if (launchConfig.ask_verbosity_on_launch) {
    initialValues.verbosity = sourceOfValues?.verbosity || 0;
  }
  if (launchConfig.ask_tags_on_launch) {
    initialValues.job_tags = sourceOfValues?.job_tags || '';
  }
  if (launchConfig.ask_skip_tags_on_launch) {
    initialValues.skip_tags = sourceOfValues?.skip_tags || '';
  }
  if (launchConfig.ask_scm_branch_on_launch) {
    initialValues.scm_branch = sourceOfValues?.scm_branch || '';
  }
  if (launchConfig.ask_diff_mode_on_launch) {
    initialValues.diff_mode = sourceOfValues?.diff_mode || false;
  }

  if (launchConfig.ask_variables_on_launch) {
    const newExtraData = { ...sourceOfValues.extra_data };
    if (launchConfig.survey_enabled && surveyConfig.spec) {
      surveyConfig.spec.forEach(question => {
        if (
          Object.prototype.hasOwnProperty.call(newExtraData, question.variable)
        ) {
          delete newExtraData[question.variable];
        }
      });
    }
    initialValues.extra_vars = jsonToYaml(JSON.stringify(newExtraData));
  }

  if (surveyConfig?.spec) {
    surveyConfig.spec.forEach(question => {
      if (question.type === 'multiselect') {
        initialValues[`survey_${question.variable}`] = question.default.split(
          '\n'
        );
      } else {
        initialValues[`survey_${question.variable}`] = question.default;
      }
      if (sourceOfValues?.extra_data) {
        Object.entries(sourceOfValues?.extra_data).forEach(([key, value]) => {
          if (key === question.variable) {
            if (question.type === 'multiselect') {
              initialValues[`survey_${question.variable}`] = value;
            } else {
              initialValues[`survey_${question.variable}`] = value;
            }
          }
        });
      }
    });
  }

  return initialValues;
};

export default function useWorkflowNodeSteps(
  launchConfig,
  surveyConfig,
  i18n,
  resource,
  askLinkType,
  resourceDefaultCredentials
) {
  const { nodeToEdit } = useContext(WorkflowStateContext);
  const {
    resetForm,
    values: formikValues,
    errors: formikErrors,
  } = useFormikContext();
  const [visited, setVisited] = useState({});

  const steps = [
    useRunTypeStep(i18n, askLinkType),
    useNodeTypeStep(launchConfig, i18n),
    useInventoryStep(launchConfig, resource, i18n, visited),
    useCredentialsStep(
      launchConfig,
      resource,
      resourceDefaultCredentials,
      i18n
    ),
    useOtherPromptsStep(launchConfig, resource, i18n),
    useSurveyStep(launchConfig, surveyConfig, resource, i18n, visited),
  ];

  const hasErrors = steps.some(step => step.hasError);

  steps.push(
    usePreviewStep(
      launchConfig,
      i18n,
      resource,
      surveyConfig,
      hasErrors,
      showPreviewStep(formikValues.nodeType, launchConfig)
    )
  );

  const pfSteps = steps.map(s => s.step).filter(s => s != null);
  const isReady = !steps.some(s => !s.isReady);

  useEffect(() => {
    if (launchConfig && surveyConfig && isReady) {
      let initialValues = {};

      if (
        nodeToEdit &&
        nodeToEdit?.fullUnifiedJobTemplate &&
        nodeToEdit?.fullUnifiedJobTemplate?.id === formikValues.nodeResource?.id
      ) {
        initialValues = getNodeToEditDefaultValues(
          launchConfig,
          surveyConfig,
          nodeToEdit,
          resourceDefaultCredentials
        );
      } else {
        initialValues = steps.reduce((acc, cur) => {
          return {
            ...acc,
            ...cur.initialValues,
          };
        }, {});
      }

      const errors = formikErrors.nodeResource
        ? {
            nodeResource: formikErrors.nodeResource,
          }
        : {};

      if (
        !launchConfig?.ask_credential_on_launch &&
        launchConfig?.passwords_needed_to_start?.length > 0
      ) {
        errors.nodeResource = i18n._(
          t`Job Templates with credentials that prompt for passwords cannot be selected when creating or editing nodes`
        );
      }

      resetForm({
        errors,
        values: {
          ...initialValues,
          nodeResource: formikValues.nodeResource,
          nodeType: formikValues.nodeType,
          linkType: formikValues.linkType,
          verbosity: initialValues?.verbosity?.toString(),
        },
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [launchConfig, surveyConfig, isReady]);

  const stepWithError = steps.find(s => s.contentError);
  const contentError = stepWithError ? stepWithError.contentError : null;

  return {
    steps: pfSteps,
    validateStep: stepId => {
      steps.find(s => s?.step?.id === stepId).validate();
    },
    visitStep: (prevStepId, setFieldTouched) => {
      setVisited({
        ...visited,
        [prevStepId]: true,
      });
      steps.find(s => s?.step?.id === prevStepId).setTouched(setFieldTouched);
    },
    visitAllSteps: setFieldTouched => {
      setVisited({
        inventory: true,
        credentials: true,
        other: true,
        survey: true,
        preview: true,
      });
      steps.forEach(s => s.setTouched(setFieldTouched));
    },
    contentError,
  };
}
