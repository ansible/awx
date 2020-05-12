import React, { useState, useEffect, useCallback } from 'react';
import { t } from '@lingui/macro';
import useRequest from '../../../util/useRequest';
import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from '../../../api';
import SurveyStep from './SurveyStep';
import StepName from './StepName';

const STEP_ID = 'survey';

export default function useSurveyStep(config, resource, visitedSteps, i18n) {
  const [stepErrors, setStepErrors] = useState({});

  const { result: survey, request: fetchSurvey, isLoading, error } = useRequest(
    useCallback(async () => {
      if (!config.survey_enabled) {
        return {};
      }
      const { data } =
        resource.type === 'workflow_job_template'
          ? await WorkflowJobTemplatesAPI.readSurvey(resource.id)
          : await JobTemplatesAPI.readSurvey(resource.id);
      return data;
    }, [config.survey_enabled, resource])
  );

  useEffect(() => {
    fetchSurvey();
  }, [fetchSurvey]);

  const validate = values => {
    if (!config.survey_enabled || !survey || !survey.spec) {
      return {};
    }
    const errors = {};
    survey.spec.forEach(question => {
      const errMessage = validateField(
        question,
        values[`survey_${question.variable}`],
        i18n
      );
      if (errMessage) {
        errors[`survey_${question.variable}`] = errMessage;
      }
    });
    setStepErrors(errors);
    return errors;
  };

  const hasErrors = visitedSteps[STEP_ID] && Object.keys(stepErrors).length > 0;

  return {
    step: getStep(config, survey, hasErrors, i18n),
    initialValues: getInitialValues(config, survey),
    validate,
    survey,
    isReady: !isLoading && !!survey,
    error,
    setTouched: setFieldsTouched => {
      if (!survey) {
        return;
      }
      const fields = {};
      survey.spec.forEach(question => {
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

function getStep(config, survey, hasErrors, i18n) {
  if (!config.survey_enabled) {
    return null;
  }
  return {
    id: STEP_ID,
    name: <StepName hasErrors={hasErrors}>{i18n._(t`Survey`)}</StepName>,
    component: <SurveyStep survey={survey} i18n={i18n} />,
  };
}

function getInitialValues(config, survey) {
  if (!config.survey_enabled || !survey) {
    return {};
  }
  const values = {};
  survey.spec.forEach(question => {
    if (question.type === 'multiselect') {
      values[`survey_${question.variable}`] = question.default.split('\n');
    } else {
      values[`survey_${question.variable}`] = question.default;
    }
  });
  return values;
}
