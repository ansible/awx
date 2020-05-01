import React, { useEffect, useCallback } from 'react';
import { t } from '@lingui/macro';
import useRequest from '@util/useRequest';
import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from '@api';
import SurveyStep from './SurveyStep';

const STEP_ID = 'survey';

export default function useSurveyStep(config, resource, i18n) {
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

  return {
    step: getStep(config, survey, i18n),
    initialValues: getInitialValues(config, survey),
    survey,
    isReady: !isLoading && !!survey,
    error,
  };
}

function getStep(config, survey, i18n) {
  if (!config.survey_enabled) {
    return null;
  }
  return {
    id: STEP_ID,
    name: i18n._(t`Survey`),
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
