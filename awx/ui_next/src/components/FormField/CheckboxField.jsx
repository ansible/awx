import React from 'react';
import { string, func } from 'prop-types';
import { Field } from 'formik';
import { Checkbox, Tooltip } from '@patternfly/react-core';
import { QuestionCircleIcon as PFQuestionCircleIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

const QuestionCircleIcon = styled(PFQuestionCircleIcon)`
  margin-left: 10px;
`;

function CheckboxField({ id, name, label, tooltip, validate, ...rest }) {
  return (
    <Field
      name={name}
      validate={validate}
      render={({ field }) => (
        <Checkbox
          aria-label={label}
          label={
            <span>
              {label}
              &nbsp;
              {tooltip && (
                <Tooltip position="right" content={tooltip}>
                  <QuestionCircleIcon />
                </Tooltip>
              )}
            </span>
          }
          id={id}
          {...rest}
          isChecked={field.value}
          {...field}
          onChange={(value, event) => {
            field.onChange(event);
          }}
        />
      )}
    />
  );
}
CheckboxField.propTypes = {
  id: string.isRequired,
  name: string.isRequired,
  label: string.isRequired,
  validate: func,
  tooltip: string,
};
CheckboxField.defaultProps = {
  validate: () => {},
  tooltip: '',
};

export default CheckboxField;
