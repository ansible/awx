import React from 'react';
import PropTypes from 'prop-types';

import {
  FormGroup,
  Select,
  SelectOption,
} from '@patternfly/react-core';

class AnsibleSelect extends React.Component {
  constructor (props) {
    super(props);
    this.onSelectChange = this.onSelectChange.bind(this);
  }

  state = {
    count: 1,
  }

  static getDerivedStateFromProps (nexProps) {
    if (nexProps.data) {
      return {
        count: nexProps.data.length,
      };
    }
    return null;
  }

  onSelectChange (val, event) {
    const { onChange, name } = this.props;
    event.target.name = name;
    onChange(val, event);
  }

  render () {
    const { count } = this.state;
    const { label = '', value, data, name, defaultSelected } = this.props;
    let elem;
    if (count > 1) {
      elem = (
        <FormGroup label={label} fieldId={`ansible-select-${name}`}>
          <Select value={value} onChange={this.onSelectChange} aria-label="Select Input">
            {data.map((datum) => (datum === defaultSelected
              ? (<SelectOption key="" value="" label={`Use Default ${label}`} />) : (<SelectOption key={datum} value={datum} label={datum} />)))
            }
          </Select>
        </FormGroup>
      );
    } else {
      elem = null;
    }
    return elem;
  }
}

AnsibleSelect.defaultProps = {
  data: [],
  label: 'Ansible Select',
  defaultSelected: null,
  name: null,
};

AnsibleSelect.propTypes = {
  data: PropTypes.arrayOf(PropTypes.string),
  defaultSelected: PropTypes.string,
  label: PropTypes.string,
  name: PropTypes.string,
  onChange: PropTypes.func.isRequired,
  value: PropTypes.string.isRequired,
};

export default AnsibleSelect;
