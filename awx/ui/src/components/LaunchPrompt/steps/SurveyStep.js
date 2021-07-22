import React, { useState } from 'react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import {
  Form,
  FormGroup,
  Select,
  SelectOption,
  SelectVariant,
} from '@patternfly/react-core';
import {
  required,
  minMaxValue,
  maxLength,
  minLength,
  integer,
  combine,
} from 'util/validators';
import { Survey } from 'types';
import FormField from '../../FormField';
import Popover from '../../Popover';

function SurveyStep({ surveyConfig }) {
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
    <Form
      onSubmit={(e) => {
        e.preventDefault();
      }}
    >
      {surveyConfig.spec.map((question) => {
        const Field = fieldTypes[question.type];
        return <Field key={question.variable} question={question} />;
      })}
    </Form>
  );
}
SurveyStep.propTypes = {
  surveyConfig: Survey.isRequired,
};

function TextField({ question }) {
  const validators = [
    question.required ? required(null) : null,
    question.required && question.min ? minLength(question.min) : null,
    question.required && question.max ? maxLength(question.max) : null,
  ];
  return (
    <FormField
      id={`survey-question-${question.variable}`}
      name={`survey_${question.variable}`}
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

function NumberField({ question }) {
  const validators = [
    question.required ? required(null) : null,
    minMaxValue(question.min, question.max),
    question.type === 'integer' ? integer() : null,
  ];
  return (
    <FormField
      id={`survey-question-${question.variable}`}
      name={`survey_${question.variable}`}
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
  const [field, meta, helpers] = useField({
    name: `survey_${question.variable}`,
    validate: question.required ? required(null) : null,
  });
  const [isOpen, setIsOpen] = useState(false);
  const id = `survey-question-${question.variable}`;
  const isValid = !(meta.touched && meta.error);

  let options = [];

  if (typeof question.choices === 'string') {
    options = question.choices.split('\n');
  } else if (Array.isArray(question.choices)) {
    options = [...question.choices];
  }

  return (
    <FormGroup
      fieldId={id}
      helperTextInvalid={meta.error}
      isRequired={question.required}
      validated={isValid ? 'default' : 'error'}
      label={question.question_name}
      labelIcon={<Popover content={question.question_description} />}
    >
      <Select
        onToggle={setIsOpen}
        onSelect={(event, option) => {
          helpers.setValue(option);
          setIsOpen(false);
        }}
        selections={field.value}
        variant={SelectVariant.single}
        id={id}
        isOpen={isOpen}
        placeholderText={t`Select an option`}
        onClear={() => {
          helpers.setTouched(true);
          helpers.setValue('');
        }}
      >
        {options.map((opt) => (
          <SelectOption key={opt} value={opt} />
        ))}
      </Select>
    </FormGroup>
  );
}

function MultiSelectField({ question }) {
  const [isOpen, setIsOpen] = useState(false);
  const [field, meta, helpers] = useField({
    name: `survey_${question.variable}`,
    validate: question.required ? required(null) : null,
  });
  const id = `survey-question-${question.variable}`;
  const hasActualValue = !question.required || meta.value?.length > 0;
  const isValid = !meta.touched || (!meta.error && hasActualValue);

  let options = [];

  if (typeof question.choices === 'string') {
    options = question.choices.split('\n');
  } else if (Array.isArray(question.choices)) {
    options = [...question.choices];
  }

  return (
    <FormGroup
      fieldId={id}
      helperTextInvalid={
        meta.error || t`At least one value must be selected for this field.`
      }
      isRequired={question.required}
      validated={isValid ? 'default' : 'error'}
      label={question.question_name}
      labelIcon={<Popover content={question.question_description} />}
    >
      <Select
        variant={SelectVariant.typeaheadMulti}
        id={id}
        placeholderText={!field.value.length && t`Select option(s)`}
        onToggle={setIsOpen}
        onSelect={(event, option) => {
          if (field?.value?.includes(option)) {
            helpers.setValue(field.value.filter((o) => o !== option));
          } else {
            helpers.setValue(field.value.concat(option));
          }
          helpers.setTouched(true);
        }}
        isOpen={isOpen}
        selections={field.value}
        onClear={() => {
          helpers.setTouched(true);
          helpers.setValue([]);
        }}
      >
        {options.map((opt) => (
          <SelectOption key={opt} value={opt} />
        ))}
      </Select>
    </FormGroup>
  );
}

export default SurveyStep;
