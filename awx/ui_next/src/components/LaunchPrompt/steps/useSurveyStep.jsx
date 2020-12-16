import React from 'react';
import { t } from '@lingui/macro';
import { useFormikContext } from 'formik';
import SurveyStep from './SurveyStep';
import StepName from './StepName';

const STEP_ID = 'survey';

export default function useSurveyStep(
  launchConfig,
  surveyConfig,
  resource,
  i18n,
  visitedSteps
) {
  const { values } = useFormikContext();
  const errors = {};
  const validate = () => {
    if (!launchConfig.survey_enabled || !surveyConfig?.spec) {
      return {};
    }
    surveyConfig.spec.forEach(question => {
      const errMessage = validateField(
        question,
        values[`survey_${question.variable}`],
        i18n
      );
      if (errMessage) {
        errors[`survey_${question.variable}`] = errMessage;
      }
    });
    return errors;
  };
  const formError = Object.keys(validate()).length > 0;
  return {
    step: getStep(launchConfig, surveyConfig, validate, i18n, visitedSteps),
    initialValues: getInitialValues(launchConfig, surveyConfig, resource),
    validate,
    surveyConfig,
    isReady: true,
    contentError: null,
    formError,
    setTouched: setFieldsTouched => {
      if (!surveyConfig?.spec) {
        return;
      }
      const fields = {};
      surveyConfig.spec.forEach(question => {
        fields[`survey_${question.variable}`] = true;
      });
      setFieldsTouched(fields);
    },
  };
}

function validateField(question, value, i18n) {
  const isTextField = ['text', 'textarea'].includes(question.type);
  const isNumeric = ['integer', 'float'].includes(question.type);
  if (isTextField && (value || value === 0)) {
    if (question.min && value.length < question.min) {
      return i18n._(t`This field must be at least ${question.min} characters`);
    }
    if (question.max && value.length > question.max) {
      return i18n._(t`This field must not exceed ${question.max} characters`);
    }
  }
  if (isNumeric && (value || value === 0)) {
    if (value < question.min || value > question.max) {
      return i18n._(
        t`This field must be a number and have a value between ${question.min} and ${question.max}`
      );
    }
  }
  if (question.required && !value && value !== 0) {
    return i18n._(t`This field must not be blank`);
  }
  return null;
}
function getStep(launchConfig, surveyConfig, validate, i18n, visitedSteps) {
  if (!launchConfig.survey_enabled) {
    return null;
  }

  return {
    id: STEP_ID,
    name: (
      <StepName
        hasErrors={
          Object.keys(visitedSteps).includes(STEP_ID) &&
          Object.keys(validate()).length
        }
        id="survey-step"
      >
        {i18n._(t`Survey`)}
      </StepName>
    ),
    component: <SurveyStep surveyConfig={surveyConfig} i18n={i18n} />,
    enableNext: true,
  };
}

function getInitialValues(launchConfig, surveyConfig, resource) {
  if (!launchConfig.survey_enabled || !surveyConfig) {
    return {};
  }

  const values = {};
  if (surveyConfig?.spec) {
    surveyConfig.spec.forEach(question => {
      if (question.type === 'multiselect') {
        values[`survey_${question.variable}`] = question.default
          ? question.default.split('\n')
          : [];
      } else if (question.type === 'multiplechoice') {
        values[`survey_${question.variable}`] =
          question.default || question.choices.split('\n')[0];
      } else {
        values[`survey_${question.variable}`] = question.default || '';
      }
      if (resource?.extra_data) {
        Object.entries(resource.extra_data).forEach(([key, value]) => {
          if (key === question.variable) {
            if (question.type === 'multiselect') {
              values[`survey_${question.variable}`] = value;
            } else {
              values[`survey_${question.variable}`] = value;
            }
          }
        });
      }
    });
  }

  return values;
}
