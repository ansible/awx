import React from 'react';
import PropTypes from 'prop-types';
import { useField } from 'formik';
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

  const [field, meta] = useField({ name, validate });
  const isValid = !(meta.touched && meta.error);

        return (
          <FormGroup
            fieldId={id}
          helperTextInvalid={meta.error}
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
            isValid={isValid}
          helperTextInvalid={meta.error}
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
    </Field>
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
