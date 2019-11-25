import React from 'react';
import {
  arrayOf,
  oneOfType,
  func,
  number,
  string,
  shape,
  bool,
} from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormSelect, FormSelectOption } from '@patternfly/react-core';

class AnsibleSelect extends React.Component {
  constructor(props) {
    super(props);
    this.onSelectChange = this.onSelectChange.bind(this);
  }

  onSelectChange(val, event) {
    const { onChange, name } = this.props;
    event.target.name = name;
    onChange(event, val);
  }

  render() {
    const { id, data, i18n, isValid, onBlur, value } = this.props;

    return (
      <FormSelect
        id={id}
        value={value}
        onChange={this.onSelectChange}
        onBlur={onBlur}
        aria-label={i18n._(t`Select Input`)}
        isValid={isValid}
      >
        {data.map(option => (
          <FormSelectOption
            key={option.id}
            value={option.value}
            label={option.label}
            isDisabled={option.isDisabled}
          />
        ))}
      </FormSelect>
    );
  }
}

const Option = shape({
  id: oneOfType([string, number]).isRequired,
  value: oneOfType([string, number]).isRequired,
  label: string.isRequired,
  isDisabled: bool,
});

AnsibleSelect.defaultProps = {
  data: [],
  isValid: true,
  onBlur: () => {},
};

AnsibleSelect.propTypes = {
  data: arrayOf(Option),
  id: string.isRequired,
  isValid: bool,
  onBlur: func,
  onChange: func.isRequired,
  value: oneOfType([string, number]).isRequired,
};

export { AnsibleSelect as _AnsibleSelect };
export default withI18n()(AnsibleSelect);
