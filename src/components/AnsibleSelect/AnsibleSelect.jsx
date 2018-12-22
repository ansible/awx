import React from 'react';

import {
  FormGroup,
  Select,
  SelectOption,
} from '@patternfly/react-core';

class AnsibleSelect extends React.Component {
  constructor(props) {
    super(props);
    this.onSelectChange = this.onSelectChange.bind(this);
  }

  state = {
    count: 1,
  }

  static getDerivedStateFromProps(nexProps, _) {
    if (nexProps.data) {
      return {
        count: nexProps.data.length,
      }
    }
    return null;
  }
  onSelectChange(val, _) {
    this.props.selectChange(val);
  }

  render() {
    const { count } = this.state;
    if (count > 1) {
      return (
        <FormGroup label={this.props.labelName} fieldId="ansible-select">
          <Select value={this.props.selected} onChange={this.onSelectChange} aria-label="Select Input">
            {this.props.data.map((datum, index) => (
              <SelectOption isDisabled={datum.disabled} key={index} value={datum} label={datum} />
            ))}
          </Select>
        </FormGroup>
      )
    }
    else {
      return null;
    }
  }
}

export default AnsibleSelect;
