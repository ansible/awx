import React, { useEffect, useCallback } from 'react';
import { t } from '@lingui/macro';
import { useFormikContext } from 'formik';
import useRequest from '../../../util/useRequest';
import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from '../../../api';
import SurveyStep from './SurveyStep';
import StepName from './StepName';

const STEP_ID = 'survey';

export default function useSurveyStep(
  config,
  i18n,
  visitedSteps,
  resource,
  nodeToEdit
) {
  const { values } = useFormikContext();
  const { result: survey, request: fetchSurvey, isLoading, error } = useRequest(
    useCallback(async () => {
      if (!config.survey_enabled) {
        return {};
      }
      const { data } = config?.workflow_job_template_data
        ? await WorkflowJobTemplatesAPI.readSurvey(
            config?.workflow_job_template_data?.id
          )
        : await JobTemplatesAPI.readSurvey(config?.job_template_data?.id);
      return data;
    }, [config])
  );

  useEffect(() => {
    fetchSurvey();
  }, [fetchSurvey]);

  const errors = {};
  const validate = () => {
    if (!config.survey_enabled || !survey || !survey.spec) {
      return {};
    }
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
    return errors;
  };
  const formError = Object.keys(validate()).length > 0;
  return {
    step: getStep(config, survey, validate, i18n, visitedSteps),
    initialValues: getInitialValues(config, survey, nodeToEdit),
    validate,
    survey,
    isReady: !isLoading && !!survey,
    contentError: error,
    formError,
    setTouched: setFieldsTouched => {
      if (!survey || !survey.spec) {
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
function getStep(config, survey, validate, i18n, visitedSteps) {
  if (!config.survey_enabled) {
    return null;
  }

  return {
    id: STEP_ID,
    key: 6,
    name: (
      <StepName
        hasErrors={
          Object.keys(visitedSteps).includes(STEP_ID) &&
          Object.keys(validate()).length
        }
      >
        {i18n._(t`Survey`)}
      </StepName>
    ),
    component: <SurveyStep survey={survey} i18n={i18n} />,
    enableNext: true,
  };
}

function getInitialValues(config, survey, nodeToEdit) {
  if (!config.survey_enabled || !survey) {
    return {};
  }

  const values = {};
  if (survey && survey.spec) {
    survey.spec.forEach(question => {
      if (question.type === 'multiselect') {
        values[`survey_${question.variable}`] = question.default.split('\n');
      } else {
        values[`survey_${question.variable}`] = question.default;
      }
      if (nodeToEdit?.extra_data) {
        Object.entries(nodeToEdit?.extra_data).forEach(([key, value]) => {
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
