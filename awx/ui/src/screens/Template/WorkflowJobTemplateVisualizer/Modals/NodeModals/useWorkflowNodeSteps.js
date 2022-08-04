import { useContext, useState, useEffect } from 'react';
import { useFormikContext } from 'formik';
import { t } from '@lingui/macro';
import useInventoryStep from 'components/LaunchPrompt/steps/useInventoryStep';
import useCredentialsStep from 'components/LaunchPrompt/steps/useCredentialsStep';
import useExecutionEnvironmentStep from 'components/LaunchPrompt/steps/useExecutionEnvironmentStep';
import useOtherPromptsStep from 'components/LaunchPrompt/steps/useOtherPromptsStep';
import useSurveyStep from 'components/LaunchPrompt/steps/useSurveyStep';
import usePreviewStep from 'components/LaunchPrompt/steps/usePreviewStep';
import { WorkflowStateContext } from 'contexts/Workflow';
import { jsonToYaml } from 'util/yaml';
import { stringIsUUID } from 'util/strings';
import useNodeTypeStep from './NodeTypeStep/useNodeTypeStep';
import useDaysToKeepStep from './useDaysToKeepStep';
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
    launchConfig.ask_execution_environment_on_launch ||
    launchConfig.ask_labels_on_launch ||
    launchConfig.ask_forks_on_launch ||
    launchConfig.ask_job_slicing_on_launch ||
    launchConfig.ask_timeout_on_launch ||
    launchConfig.ask_instance_groups_on_launch ||
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
  let identifier = '';
  if (
    Object.prototype.hasOwnProperty.call(nodeToEdit, 'identifier') &&
    nodeToEdit.identifier !== null
  ) {
    ({ identifier } = nodeToEdit);
  } else if (
    Object.prototype.hasOwnProperty.call(
      nodeToEdit?.originalNodeObject,
      'identifier'
    ) &&
    !stringIsUUID(nodeToEdit?.originalNodeObject?.identifier)
  ) {
    identifier = nodeToEdit?.originalNodeObject?.identifier;
  }

  const getConvergence = () => {
    // There is a case where the nodeToEdit convergence value will not align with the
    // original node object value.  This allows the nodeToEdit value to take precedence over the
    // original node object.
    if (nodeToEdit) {
      return nodeToEdit.all_parents_must_converge ? 'all' : 'any';
    }
    return nodeToEdit?.originalNodeObject?.all_parents_must_converge
      ? 'all'
      : 'any';
  };
  const initialValues = {
    nodeResource: nodeToEdit?.fullUnifiedJobTemplate || null,
    nodeType: nodeToEdit?.fullUnifiedJobTemplate?.type || 'job_template',
    convergence: getConvergence(),
    identifier,
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

  if (nodeToEdit?.fullUnifiedJobTemplate?.type === 'system_job_template') {
    if (
      nodeToEdit?.promptValues?.extra_data &&
      Object.prototype.hasOwnProperty.call(
        nodeToEdit.promptValues.extra_data,
        'days'
      )
    ) {
      initialValues.daysToKeep = parseInt(
        nodeToEdit.promptValues.extra_data.days,
        10
      );
    } else if (
      nodeToEdit?.originalNodeObject?.extra_data &&
      Object.prototype.hasOwnProperty.call(
        nodeToEdit.originalNodeObject.extra_data,
        'days'
      )
    ) {
      initialValues.daysToKeep = parseInt(
        nodeToEdit.originalNodeObject.extra_data.days,
        10
      );
    }

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

  if (launchConfig.ask_execution_environment_on_launch) {
    if (nodeToEdit?.promptValues) {
      initialValues.execution_environment =
        nodeToEdit?.promptValues?.execution_environment;
    } else if (
      nodeToEdit?.originalNodeObject?.summary_fields?.execution_environment
    ) {
      initialValues.execution_environment =
        nodeToEdit?.originalNodeObject?.summary_fields?.execution_environment;
    } else {
      initialValues.execution_environment = null;
    }
  }

  if (launchConfig.ask_credential_on_launch) {
    if (nodeToEdit?.promptValues?.credentials) {
      initialValues.credentials = nodeToEdit?.promptValues?.credentials;
    } else if (nodeToEdit?.originalNodeCredentials) {
      const defaultCredsWithoutOverrides = [];

      const credentialHasOverride = (templateDefaultCred) => {
        let hasOverride = false;
        nodeToEdit.originalNodeCredentials.forEach((nodeCredential) => {
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
        resourceDefaultCredentials.forEach((defaultCred) => {
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
  if (launchConfig.ask_forks_on_launch) {
    initialValues.forks = sourceOfValues?.forks || 0;
  }
  if (launchConfig.ask_job_slicing_on_launch) {
    initialValues.job_slice_count = sourceOfValues?.job_slice_count || 1;
  }
  if (launchConfig.ask_timeout_on_launch) {
    initialValues.timeout = sourceOfValues?.timeout || 0;
  }

  if (launchConfig.ask_variables_on_launch) {
    const newExtraData = { ...sourceOfValues.extra_data };
    if (launchConfig.survey_enabled && surveyConfig.spec) {
      surveyConfig.spec.forEach((question) => {
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
    surveyConfig.spec.forEach((question) => {
      if (question.type === 'multiselect') {
        initialValues[`survey_${question.variable}`] =
          question.default.split('\n');
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
    useRunTypeStep(askLinkType),
    useNodeTypeStep(launchConfig),
    useDaysToKeepStep(),
    useInventoryStep(launchConfig, resource, visited),
    useCredentialsStep(launchConfig, resource, resourceDefaultCredentials),
    useExecutionEnvironmentStep(launchConfig, resource),
    useOtherPromptsStep(launchConfig, resource),
    useSurveyStep(launchConfig, surveyConfig, resource, visited),
  ];

  const hasErrors = steps.some((step) => step.hasError);

  steps.push(
    usePreviewStep(
      launchConfig,
      resource,
      surveyConfig,
      hasErrors,
      showPreviewStep(formikValues.nodeType, launchConfig)
    )
  );

  const pfSteps = steps.map((s) => s.step).filter((s) => s != null);
  const isReady = !steps.some((s) => !s.isReady);

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
        initialValues = steps.reduce(
          (acc, cur) => ({
            ...acc,
            ...cur.initialValues,
          }),
          {}
        );
        initialValues.identifier = formikValues.identifier;
        initialValues.convergence = formikValues.convergence;
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
        errors.nodeResource = t`Job Templates with credentials that prompt for passwords cannot be selected when creating or editing nodes`;
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
  const stepWithError = steps.find((s) => s.contentError);
  const contentError = stepWithError ? stepWithError.contentError : null;

  return {
    steps: pfSteps,
    validateStep: (stepId) => {
      steps.find((s) => s?.step?.id === stepId).validate();
    },
    visitStep: (prevStepId, setFieldTouched) => {
      setVisited({
        ...visited,
        [prevStepId]: true,
      });
      steps.find((s) => s?.step?.id === prevStepId).setTouched(setFieldTouched);
    },
    visitAllSteps: (setFieldTouched) => {
      setVisited({
        inventory: true,
        credentials: true,
        executionEnvironment: true,
        other: true,
        survey: true,
        preview: true,
      });
      steps.forEach((s) => s.setTouched(setFieldTouched));
    },
    contentError,
  };
}
