import React, { useCallback, useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { useField } from 'formik';
import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from '@api';
import { Form } from '@patternfly/react-core';
import FormField from '@components/FormField';
import AnsibleSelect from '@components/AnsibleSelect';
import ContentLoading from '@components/ContentLoading';
import ContentError from '@components/ContentError';
import useRequest from '@util/useRequest';
import {
  required,
  minMaxValue,
  maxLength,
  minLength,
  integer,
  combine,
} from '@util/validators';

function SurveyStep({ template, i18n }) {
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

  const fieldTypes = {
    text: TextField,
    textarea: TextField,
    password: TextField,
    multiplechoice: MultipleChoiceField,
    multiselect: MultiSelectField,
    integer: NumberField,
    float: NumberField,
  };
  return (
    <Form>
      {survey.spec.map(question => {
        const Field = fieldTypes[question.type];
        return (
          <Field key={question.variable} question={question} i18n={i18n} />
        );
      })}
    </Form>
  );
}

function TextField({ question, i18n }) {
  const validators = [
    question.required ? required(null, i18n) : null,
    question.min ? minLength(question.min, i18n) : null,
    question.max ? maxLength(question.max, i18n) : null,
  ];
  return (
    <FormField
      id={`survey-question-${question.variable}`}
      name={question.variable}
      label={question.question_name}
      tooltip={question.question_description}
      isRequired={question.required}
      validate={combine(validators)}
      type={question.type}
      minLength={question.min}
      maxLength={question.max}
    />
  );
}

function NumberField({ question, i18n }) {
  const validators = [
    question.required ? required(null, i18n) : null,
    minMaxValue(question.min, question.max, i18n),
    question.type === 'integer' ? integer(i18n) : null,
  ];
  return (
    <FormField
      id={`survey-question-${question.variable}`}
      name={question.variable}
      label={question.question_name}
      tooltip={question.question_description}
      isRequired={question.required}
      validate={combine(validators)}
      type="number"
      min={question.min}
      max={question.max}
    />
  );
}

function MultipleChoiceField({ question, i18n }) {
  const [field, meta] = useField(question.question_name);
  console.log(question, field);
  return (
    <AnsibleSelect
      id={`survey-question-${question.variable}`}
      isValid={!meta.errors}
      {...field}
      data={question.choices.split('/n').map(opt => ({
        key: opt,
        value: opt,
        label: opt,
      }))}
    />
  );
}

function MultiSelectField({ question, i18n }) {
  const [field, meta] = useField(question.question_name);
  return (
    <AnsibleSelect
      id={`survey-question-${question.variable}`}
      isValid={!meta.errors}
      {...field}
      data={question.choices.split('/n').map(opt => ({
        key: opt,
        value: opt,
        label: opt,
      }))}
    />
  );
}

export default withI18n()(SurveyStep);
