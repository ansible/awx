import React from 'react';
import { useFormikContext } from 'formik';
import yaml from 'js-yaml';
import PromptDetail from '@components/PromptDetail';
import mergeExtraVars, { maskPasswords } from './mergeExtraVars';

function PreviewStep({ resource, config, survey, formErrors }) {
  const { values } = useFormikContext();
  const passwordFields = survey.spec
    .filter(q => q.type === 'password')
    .map(q => q.variable);
  const masked = maskPasswords(values.survey, passwordFields);
  return (
    <>
      <PromptDetail
        resource={resource}
        launchConfig={config}
        overrides={{
          ...values,
          extra_vars: yaml.safeDump(mergeExtraVars(values.extra_vars, masked)),
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
