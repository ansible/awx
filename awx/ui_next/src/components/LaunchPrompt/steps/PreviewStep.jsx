import React from 'react';
import { useFormikContext } from 'formik';
import yaml from 'js-yaml';
import PromptDetail from '../../PromptDetail';
import mergeExtraVars, { maskPasswords } from '../mergeExtraVars';
import getSurveyValues from '../getSurveyValues';

function PreviewStep({ resource, config, survey, formErrors }) {
  const { values } = useFormikContext();
  const surveyValues = getSurveyValues(values);

  const overrides = { ...values };

  if (config.ask_variables_on_launch || config.survey_enabled) {
    const initialExtraVars = config.ask_variables_on_launch
      ? values.extra_vars || '---'
      : resource.extra_vars;
    if (survey && survey.spec) {
      const passwordFields = survey.spec
        .filter(q => q.type === 'password')
        .map(q => q.variable);
      const masked = maskPasswords(surveyValues, passwordFields);
      overrides.extra_vars = yaml.safeDump(
        mergeExtraVars(initialExtraVars, masked)
      );
    } else {
      overrides.extra_vars = initialExtraVars;
    }
  }

  return (
    <>
      <PromptDetail
        resource={resource}
        launchConfig={config}
        overrides={overrides}
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
