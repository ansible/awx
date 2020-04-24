import React from 'react';
import { useFormikContext } from 'formik';
import PromptDetail from '@components/PromptDetail';
import { encodeExtraVars } from './mergeExtraVars';

function PreviewStep({ resource, config, survey }) {
  const { values } = useFormikContext();
  return (
    <PromptDetail
      resource={resource}
      launchConfig={config}
      promptResponses={{
        ...values,
        extra_vars: encodeExtraVars(values.extra_vars, values.survey),
      }}
    />
  );
}

export default PreviewStep;
