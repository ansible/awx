import React from 'react';
import { Wizard } from '@patternfly/react-core';

import { t } from '@lingui/macro';
import { useFormikContext } from 'formik';
import AlertModal from '../../AlertModal';
import { useDismissableError } from '../../../util/useRequest';
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
}) {
  const {
    setFieldTouched,
    values,
    initialValues,
    resetForm,
  } = useFormikContext();
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
    resourceDefaultCredentials
  );

  const { error, dismissError } = useDismissableError(contentError);
  const cancelPromptableValues = async () => {
    resetForm({
      values: {
        ...initialValues,
        daysOfWeek: values.daysOfWeek,
        description: values.description,
        end: values.end,
        endDateTime: values.endDateTime,
        frequency: values.frequency,
        interval: values.interval,
        name: values.name,
        occurences: values.occurances,
        runOn: values.runOn,
        runOnDayMonth: values.runOnDayMonth,
        runOnDayNumber: values.runOnDayNumber,
        runOnTheDay: values.runOnTheDay,
        runOnTheMonth: values.runOnTheMonth,
        runOnTheOccurence: values.runOnTheOccurance,
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
      onBack={async nextStep => {
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
      title={t`Prompts`}
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
