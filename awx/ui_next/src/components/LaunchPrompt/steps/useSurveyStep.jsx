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
  const { setFieldError, values } = useFormikContext();
  const hasError =
    Object.keys(visitedSteps).includes(STEP_ID) &&
    checkForError(launchConfig, surveyConfig, values);

  return {
    step: launchConfig.survey_enabled
      ? {
          id: STEP_ID,
          name: (
            <StepName hasErrors={hasError} id="survey-step">
              {i18n._(t`Survey`)}
            </StepName>
          ),
          component: <SurveyStep surveyConfig={surveyConfig} i18n={i18n} />,
          enableNext: true,
        }
      : null,
    initialValues: getInitialValues(launchConfig, surveyConfig, resource),
    surveyConfig,
    isReady: true,
    contentError: null,
    hasError,
    setTouched: setFieldTouched => {
      if (!surveyConfig?.spec) {
        return;
      }
      surveyConfig.spec.forEach(question => {
        setFieldTouched(`survey_${question.variable}`, true, false);
      });
    },
    validate: () => {
      if (launchConfig.survey_enabled && surveyConfig.spec) {
        surveyConfig.spec.forEach(question => {
          const errMessage = validateSurveyField(
            question,
            values[`survey_${question.variable}`],
            i18n
          );
          if (errMessage) {
            setFieldError(`survey_${question.variable}`, errMessage);
          }
        });
      }
    },
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

function validateSurveyField(question, value, i18n) {
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

function checkForError(launchConfig, surveyConfig, values) {
  let hasError = false;
  if (launchConfig.survey_enabled && surveyConfig.spec) {
    surveyConfig.spec.forEach(question => {
      const value = values[`survey_${question.variable}`];
      const isTextField = ['text', 'textarea'].includes(question.type);
      const isNumeric = ['integer', 'float'].includes(question.type);
      if (isTextField && (value || value === 0)) {
        if (
          (question.min && value.length < question.min) ||
          (question.max && value.length > question.max)
        ) {
          hasError = true;
        }
      }
      if (isNumeric && (value || value === 0)) {
        if (value < question.min || value > question.max) {
          hasError = true;
        }
      }
      if (question.required && !value && value !== 0) {
        hasError = true;
      }
    });
  }

  return hasError;
}
