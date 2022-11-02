import React, { useState } from 'react';
import { ExpandableSection, Wizard } from '@patternfly/react-core';
import { t } from '@lingui/macro';
import { useFormikContext } from 'formik';
import { useDismissableError } from 'hooks/useRequest';
import AlertModal from '../../AlertModal';
import ContentError from '../../ContentError';
import ContentLoading from '../../ContentLoading';
import useSchedulePromptSteps from './useSchedulePromptSteps';

function SchedulePromptableFields({
  schedule,
  surveyConfig,
  launchConfig,
  onCloseWizard,
  onSave,
  credentials,
  resource,
  resourceDefaultCredentials,
  labels,
  instanceGroups,
}) {
  const { setFieldTouched, values, initialValues, resetForm } =
    useFormikContext();
  const {
    steps,
    visitStep,
    visitAllSteps,
    validateStep,
    contentError,
    isReady,
  } = useSchedulePromptSteps(
    surveyConfig,
    launchConfig,
    schedule,
    resource,
    credentials,
    resourceDefaultCredentials,
    labels,
    instanceGroups
  );
  const [showDescription, setShowDescription] = useState(false);
  const { error, dismissError } = useDismissableError(contentError);
  const cancelPromptableValues = async () => {
    resetForm({
      values: {
        ...initialValues,
        description: values.description,
        frequency: values.frequency,
        name: values.name,
        startDateTime: values.startDateTime,
        timezone: values.timezone,
      },
    });
    onCloseWizard();
  };

  if (error) {
    return (
      <AlertModal
        isOpen={error}
        variant="error"
        title={t`Error!`}
        onClose={() => {
          dismissError();
          onCloseWizard();
        }}
      >
        <ContentError error={error} />
      </AlertModal>
    );
  }
  return (
    <Wizard
      isOpen
      onClose={cancelPromptableValues}
      onSave={onSave}
      onBack={async (nextStep) => {
        validateStep(nextStep.id);
      }}
      onNext={async (nextStep, prevStep) => {
        if (nextStep.id === 'preview') {
          visitAllSteps(setFieldTouched);
        } else {
          visitStep(prevStep.prevId, setFieldTouched);
          validateStep(nextStep.id);
        }
      }}
      onGoToStep={async (nextStep, prevStep) => {
        if (nextStep.id === 'preview') {
          visitAllSteps(setFieldTouched);
        } else {
          visitStep(prevStep.prevId, setFieldTouched);
          validateStep(nextStep.id);
        }
      }}
      title={t`Prompt | ${resource.name}`}
      description={
        resource.description.length > 512 ? (
          <ExpandableSection
            toggleText={
              showDescription ? t`Hide description` : t`Show description`
            }
            onToggle={() => {
              setShowDescription(!showDescription);
            }}
            isExpanded={showDescription}
          >
            {resource.description}
          </ExpandableSection>
        ) : (
          resource.description
        )
      }
      steps={
        isReady
          ? steps
          : [
              {
                name: t`Content Loading`,
                component: <ContentLoading />,
              },
            ]
      }
      backButtonText={t`Back`}
      cancelButtonText={t`Cancel`}
      nextButtonText={t`Next`}
    />
  );
}

export default SchedulePromptableFields;
