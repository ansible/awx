import React, { useCallback, useEffect, useState } from 'react';
import { withI18n } from '@lingui/react';
import { Formik, useField } from 'formik';
import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from '@api';
import {
  Form,
  FormGroup,
  Select,
  SelectOption,
  SelectVariant,
} from '@patternfly/react-core';
import FormField, { FieldTooltip } from '@components/FormField';
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

  const initialValues = {};
  survey.spec.forEach(question => {
    if (question.type === 'multiselect') {
      initialValues[question.variable] = question.default.split('\n');
    } else {
      initialValues[question.variable] = question.default;
    }
  });

  return (
    <SurveySubForm survey={survey} initialValues={initialValues} i18n={i18n} />
  );
}

function SurveySubForm({ survey, initialValues, i18n }) {
  const [, , surveyFieldHelpers] = useField('survey');
  useEffect(() => {
    surveyFieldHelpers.setValue(initialValues);
    /* eslint-disable-next-line react-hooks/exhaustive-deps */
  }, []);

  const fieldTypes = {
    text: TextField,
    textarea: TextField,
    password: TextField,
    multiplechoice: MultipleChoiceField,
    multiselect: MultiSelectField,
    integer: NumberField,
    float: NumberField,
  };
  // This is a nested Formik form to perform validation on individual
  // survey questions. When changes to the inner form occur (onBlur), the
  // values for all questions are added to the outer form's `survey` field
  // as a single object.
  return (
    <Formik initialValues={initialValues}>
      {({ values }) => (
        <Form onBlur={() => surveyFieldHelpers.setValue(values)}>
          {' '}
          {survey.spec.map(question => {
            const Field = fieldTypes[question.type];
            return (
              <Field key={question.variable} question={question} i18n={i18n} />
            );
          })}
        </Form>
      )}
    </Formik>
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

function MultipleChoiceField({ question }) {
  const [field, meta] = useField(question.variable);
  const id = `survey-question-${question.variable}`;
  const isValid = !(meta.touched && meta.error);
  return (
    <FormGroup
      fieldId={id}
      helperTextInvalid={meta.error}
      isRequired={question.required}
      isValid={isValid}
      label={question.question_name}
    >
      <FieldTooltip content={question.question_description} />
      <AnsibleSelect
        id={id}
        isValid={isValid}
        {...field}
        data={question.choices.split('\n').map(opt => ({
          key: opt,
          value: opt,
          label: opt,
        }))}
      />
    </FormGroup>
  );
}

function MultiSelectField({ question }) {
  const [isOpen, setIsOpen] = useState(false);
  const [field, meta, helpers] = useField(question.variable);
  const id = `survey-question-${question.variable}`;
  const isValid = !(meta.touched && meta.error);
  return (
    <FormGroup
      fieldId={id}
      helperTextInvalid={meta.error}
      isRequired={question.required}
      isValid={isValid}
      label={question.question_name}
    >
      <FieldTooltip content={question.question_description} />
      <Select
        variant={SelectVariant.typeaheadMulti}
        id={id}
        onToggle={setIsOpen}
        onSelect={(event, option) => {
          if (field.value.includes(option)) {
            helpers.setValue(field.value.filter(o => o !== option));
          } else {
            helpers.setValue(field.value.concat(option));
          }
        }}
        isExpanded={isOpen}
        selections={field.value}
      >
        {question.choices.split('\n').map(opt => (
          <SelectOption key={opt} value={opt} />
        ))}
      </Select>
    </FormGroup>
  );
}

export default withI18n()(SurveyStep);
