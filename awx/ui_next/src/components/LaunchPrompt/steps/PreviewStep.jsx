import React, { Fragment } from 'react';
import styled from 'styled-components';
import { ExclamationCircleIcon as PFExclamationCircleIcon } from '@patternfly/react-icons';
import { Tooltip } from '@patternfly/react-core';
import { t } from '@lingui/macro';
import { useFormikContext } from 'formik';
import { withI18n } from '@lingui/react';
import yaml from 'js-yaml';
import mergeExtraVars, {
  maskPasswords,
} from '../../../util/prompt/mergeExtraVars';
import getSurveyValues from '../../../util/prompt/getSurveyValues';
import PromptDetail from '../../PromptDetail';

const ExclamationCircleIcon = styled(PFExclamationCircleIcon)`
  margin-left: 10px;
  margin-top: -2px;
`;

const ErrorMessageWrapper = styled.div`
  align-items: center;
  color: var(--pf-global--danger-color--200);
  display: flex;
  font-weight: var(--pf-global--FontWeight--bold);
  margin-bottom: 10px;
`;

function PreviewStep({
  resource,
  launchConfig,
  surveyConfig,
  formErrors,
  i18n,
}) {
  const { values } = useFormikContext();
  const surveyValues = getSurveyValues(values);

  const overrides = {
    ...values,
  };

  if (launchConfig.ask_variables_on_launch || launchConfig.survey_enabled) {
    const initialExtraVars =
      launchConfig.ask_variables_on_launch && (overrides.extra_vars || '---');
    if (surveyConfig?.spec) {
      const passwordFields = surveyConfig.spec
        .filter(q => q.type === 'password')
        .map(q => q.variable);
      const masked = maskPasswords(surveyValues, passwordFields);
      overrides.extra_vars = yaml.safeDump(
        mergeExtraVars(initialExtraVars, masked)
      );
    } else {
      overrides.extra_vars = yaml.safeDump(
        mergeExtraVars(initialExtraVars, {})
      );
    }
  }

  return (
    <Fragment>
      {formErrors && (
        <ErrorMessageWrapper>
          {i18n._(t`Some of the previous step(s) have errors`)}
          <Tooltip
            position="right"
            content={i18n._(t`See errors on the left`)}
            trigger="click mouseenter focus"
          >
            <ExclamationCircleIcon />
          </Tooltip>
        </ErrorMessageWrapper>
      )}
      <PromptDetail
        resource={resource}
        launchConfig={launchConfig}
        overrides={overrides}
      />
    </Fragment>
  );
}

export default withI18n()(PreviewStep);
