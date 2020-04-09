import React, { useCallback, useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from '@api';
import { Form } from '@patternfly/react-core';
import FormField from '@components/FormField';
import ContentLoading from '@components/ContentLoading';
import ContentError from '@components/ContentError';
import useRequest from '@util/useRequest';
import { required } from '@util/validators';

function InventoryStep({ template, i18n }) {
  const { result: survey, request: fetchSurvey, isLoading, error } = useRequest(
    useCallback(async () => {
      const { data } =
        template.type === 'workflow_job_template'
          ? await WorkflowJobTemplatesAPI.readSurvey(template.id)
          : await JobTemplatesAPI.readSurvey(template.id);
      return data;
    }, [template])
  );
  useEffect(() => {
    fetchSurvey();
  }, [fetchSurvey]);

  if (error) {
    return <ContentError error={error} />;
  }
  if (isLoading || !survey) {
    return <ContentLoading />;
  }

  return (
    <Form>
      {survey.spec.map(question => (
        <SurveyQuestion
          key={question.variable}
          question={question}
          i18n={i18n}
        />
      ))}
    </Form>
  );
}

function SurveyQuestion({ question, i18n }) {
  const isNumeric = question.type === 'number' || question.type === 'integer';
  return (
    <FormField
      id={`survey-question-${question.variable}`}
      name={question.variable}
      label={question.question_name}
      tooltip={question.question_description}
      isRequired={question.required}
      validate={question.required ? required(null, i18n) : null}
      type={isNumeric ? 'number' : question.type}
      min={isNumeric ? question.min : null}
      max={isNumeric ? question.max : null}
      minLength={!isNumeric ? question.min : null}
      maxLength={!isNumeric ? question.max : null}
    />
  );
}

export default withI18n()(InventoryStep);
