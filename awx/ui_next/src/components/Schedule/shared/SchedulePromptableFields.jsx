import React from 'react';
import { Wizard } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
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
  i18n,
}) {
  const {
    validateForm,
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
    i18n,
    credentials
  );

  const { error, dismissError } = useDismissableError(contentError);
  const cancelPromptableValues = async () => {
    const hasErrors = await validateForm();
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
    onCloseWizard(Object.keys(hasErrors).length > 0);
  };

  if (error) {
    return (
      <AlertModal
        isOpen={error}
        variant="error"
        title={i18n._(t`Error!`)}
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
      onNext={async (nextStep, prevStep) => {
        if (nextStep.id === 'preview') {
          visitAllSteps(setFieldTouched);
        } else {
          visitStep(prevStep.prevId, setFieldTouched);
        }
        await validateForm();
      }}
      onGoToStep={async (nextStep, prevStep) => {
        if (nextStep.id === 'preview') {
          visitAllSteps(setFieldTouched);
        } else {
          visitStep(prevStep.prevId, setFieldTouched);
          validateStep(nextStep.id);
        }
        await validateForm();
      }}
      title={i18n._(t`Prompts`)}
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
      backButtonText={i18n._(t`Back`)}
      cancelButtonText={i18n._(t`Cancel`)}
      nextButtonText={i18n._(t`Next`)}
    />
  );
}

export default withI18n()(SchedulePromptableFields);
