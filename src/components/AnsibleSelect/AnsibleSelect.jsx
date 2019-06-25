import React from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  FormSelect,
  FormSelectOption,
} from '@patternfly/react-core';

class AnsibleSelect extends React.Component {
  constructor (props) {
    super(props);
    this.onSelectChange = this.onSelectChange.bind(this);
  }

  onSelectChange (val, event) {
    const { onChange, name } = this.props;
    event.target.name = name;
    onChange(event, val);
  }

  render () {
    const { value, data, i18n } = this.props;

    return (
      <FormSelect
        value={value}
        onChange={this.onSelectChange}
        aria-label={i18n._(t`Select Input`)}
      >
        {data.map((datum) => (
          <FormSelectOption
            key={datum.value}
            value={datum.value}
            label={datum.label}
            isDisabled={datum.isDisabled}
          />
        ))}
      </FormSelect>
    );
  }
}

AnsibleSelect.defaultProps = {
  data: [],
};

AnsibleSelect.propTypes = {
  data: PropTypes.arrayOf(PropTypes.object),
  onChange: PropTypes.func.isRequired,
  value: PropTypes.string.isRequired,
};

export { AnsibleSelect as _AnsibleSelect };
export default withI18n()(AnsibleSelect);
