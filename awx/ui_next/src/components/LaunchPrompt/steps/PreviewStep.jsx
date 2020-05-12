import React from 'react';
import { useFormikContext } from 'formik';
import yaml from 'js-yaml';
import PromptDetail from '../../PromptDetail';
import mergeExtraVars, { maskPasswords } from '../mergeExtraVars';
import getSurveyValues from '../getSurveyValues';

function PreviewStep({ resource, config, survey, formErrors }) {
  const { values } = useFormikContext();
  const surveyValues = getSurveyValues(values);
  let extraVars;
  if (survey && survey.spec) {
    const passwordFields = survey.spec
      .filter(q => q.type === 'password')
      .map(q => q.variable);
    const masked = maskPasswords(surveyValues, passwordFields);
    extraVars = yaml.safeDump(mergeExtraVars(values.extra_vars, masked));
  } else {
    extraVars = values.extra_vars;
  }
  return (
    <>
      <PromptDetail
        resource={resource}
        launchConfig={config}
        overrides={{
          ...values,
          extra_vars: extraVars,
        }}
      />
      {formErrors && (
        <ul css="color: red">
          {Object.keys(formErrors).map(
            field => `${field}: ${formErrors[field]}`
          )}
        </ul>
      )}
    </>
  );
}

export default PreviewStep;
