import React from 'react';
import { Wizard } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Formik } from 'formik';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import mergeExtraVars from './mergeExtraVars';
import useSteps from './useSteps';
import getSurveyValues from './getSurveyValues';

function LaunchPrompt({ config, resource, onLaunch, onCancel, i18n }) {
  const {
    steps,
    initialValues,
    isReady,
    validate,
    visitStep,
    visitAllSteps,
    contentError,
  } = useSteps(config, resource, i18n);

  if (contentError) {
    return <ContentError error={contentError} />;
  }
  if (!isReady) {
    return <ContentLoading />;
  }

  const submit = values => {
    const postValues = {};
    const setValue = (key, value) => {
      if (typeof value !== 'undefined' && value !== null) {
        postValues[key] = value;
      }
    };
    const surveyValues = getSurveyValues(values);
    setValue('inventory_id', values.inventory?.id);
    setValue('credentials', values.credentials?.map(c => c.id));
    setValue('job_type', values.job_type);
    setValue('limit', values.limit);
    setValue('job_tags', values.job_tags);
    setValue('skip_tags', values.skip_tags);
    setValue('extra_vars', mergeExtraVars(values.extra_vars, surveyValues));
    onLaunch(postValues);
  };

  return (
    <Formik initialValues={initialValues} onSubmit={submit} validate={validate}>
      {({ validateForm, setTouched, handleSubmit }) => (
        <Wizard
          isOpen
          onClose={onCancel}
          onSave={handleSubmit}
          onNext={async (nextStep, prevStep) => {
            if (nextStep.id === 'preview') {
              visitAllSteps(setTouched);
            } else {
              visitStep(prevStep.prevId);
            }
            await validateForm();
          }}
          onGoToStep={async (newStep, prevStep) => {
            if (newStep.id === 'preview') {
              visitAllSteps(setTouched);
            } else {
              visitStep(prevStep.prevId);
            }
            await validateForm();
          }}
          title={i18n._(t`Prompts`)}
          steps={steps}
        />
      )}
    </Formik>
  );
}

export { LaunchPrompt as _LaunchPrompt };
export default withI18n()(LaunchPrompt);
