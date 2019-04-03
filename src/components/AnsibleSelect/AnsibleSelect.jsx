import React from 'react';
import PropTypes from 'prop-types';
import { I18n } from '@lingui/react';
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
    const { label, value, data, defaultSelected } = this.props;
    return (
      <I18n>
        {({ i18n }) => (
          <FormSelect
            value={value}
            onChange={this.onSelectChange}
            aria-label={i18n._(t`Select Input`)}
          >
            {data.map((datum) => (
              datum === defaultSelected ? (
                <FormSelectOption
                  key=""
                  value=""
                  label={i18n._(t`Use Default ${label}`)}
                />
              ) : (
                <FormSelectOption key={datum} value={datum} label={datum} />
              )
            ))}
          </FormSelect>
        )}
      </I18n>
    );
  }
}

AnsibleSelect.defaultProps = {
  data: [],
  label: 'Ansible Select',
  defaultSelected: null,
};

AnsibleSelect.propTypes = {
  data: PropTypes.arrayOf(PropTypes.string),
  defaultSelected: PropTypes.string,
  label: PropTypes.string,
  name: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  value: PropTypes.string.isRequired,
};

export default AnsibleSelect;
