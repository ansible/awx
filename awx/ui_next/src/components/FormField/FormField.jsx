import React from 'react';
import PropTypes from 'prop-types';
import { Field } from 'formik';
import { FormGroup, TextInput, Tooltip } from '@patternfly/react-core';
import { QuestionCircleIcon as PFQuestionCircleIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

const QuestionCircleIcon = styled(PFQuestionCircleIcon)`
  margin-left: 10px;
`;

function FormField(props) {
  const {
    id,
    name,
    label,
    tooltip,
    tooltipMaxWidth,
    validate,
    isRequired,
    ...rest
  } = props;

  return (
    <Field
      name={name}
      validate={validate}
      render={({ field, form }) => {
        const isValid =
          form && (!form.touched[field.name] || !form.errors[field.name]);

        return (
          <FormGroup
            fieldId={id}
            helperTextInvalid={form.errors[field.name]}
            isRequired={isRequired}
            isValid={isValid}
            label={label}
          >
            {tooltip && (
              <Tooltip
                content={tooltip}
                maxWidth={tooltipMaxWidth}
                position="right"
              >
                <QuestionCircleIcon />
              </Tooltip>
            )}
            <TextInput
              id={id}
              isRequired={isRequired}
              isValid={isValid}
              {...rest}
              {...field}
              onChange={(value, event) => {
                field.onChange(event);
              }}
            />
          </FormGroup>
        );
      }}
    />
  );
}

FormField.propTypes = {
  id: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  type: PropTypes.string,
  validate: PropTypes.func,
  isRequired: PropTypes.bool,
  tooltip: PropTypes.node,
  tooltipMaxWidth: PropTypes.string,
};

FormField.defaultProps = {
  type: 'text',
  validate: () => {},
  isRequired: false,
  tooltip: null,
  tooltipMaxWidth: '',
};

export default FormField;
