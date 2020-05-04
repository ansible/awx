import React, { useState, useCallback, useEffect } from 'react';
import { Wizard } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Formik } from 'formik';
// import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from '@api';
// import useRequest from '@util/useRequest';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
// import { required } from '@util/validators';
// import InventoryStep from './InventoryStep';
// import CredentialsStep from './CredentialsStep';
// import OtherPromptsStep from './OtherPromptsStep';
// import SurveyStep from './SurveyStep';
// import PreviewStep from './PreviewStep';
// import PromptFooter from './PromptFooter';
import mergeExtraVars from './mergeExtraVars';
import { useSteps, useVisitedSteps } from './hooks';

function LaunchPrompt({ config, resource, onLaunch, onCancel, i18n }) {
  // const [formErrors, setFormErrors] = useState({});
  const {
    steps,
    initialValues,
    isReady,
    validate,
    formErrors,
    contentError,
  } = useSteps(config, resource, i18n);
  const [visitedSteps, visitStep] = useVisitedSteps(config);

  if (contentError) {
    return <ContentError error={contentError} />;
  }
  if (!isReady) {
    return <ContentLoading />;
  }

  // TODO move into hook?
  // const validate = values => {
  //   // return {};
  //   return { limit: ['required field'] };
  // };

  // TODO move into hook?
  const submit = values => {
    const postValues = {};
    const setValue = (key, value) => {
      if (typeof value !== 'undefined' && value !== null) {
        postValues[key] = value;
      }
    };
    setValue('inventory_id', values.inventory?.id);
    setValue('credentials', values.credentials?.map(c => c.id));
    setValue('job_type', values.job_type);
    setValue('limit', values.limit);
    setValue('job_tags', values.job_tags);
    setValue('skip_tags', values.skip_tags);
    setValue('extra_vars', mergeExtraVars(values.extra_vars, values.survey));
    onLaunch(postValues);
  };

  return (
    <Formik initialValues={initialValues} onSubmit={submit} validate={validate}>
      {({ errors, values, touched, validateForm, handleSubmit }) => (
        <Wizard
          isOpen
          onClose={onCancel}
          onSave={handleSubmit}
          onNext={async (nextStep, prevStep) => {
            console.log(prevStep);
            visitStep(prevStep.id);
            const newErrors = await validateForm();
            // updatePromptErrors(prevStep.prevName, newErrors);
          }}
          onGoToStep={async (newStep, prevStep) => {
            console.log(prevStep);
            visitStep(prevStep.id);
            const newErrors = await validateForm();
            // updatePromptErrors(prevStep.prevName, newErrors);
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
