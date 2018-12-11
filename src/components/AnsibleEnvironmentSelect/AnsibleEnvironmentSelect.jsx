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

  onSelectChange(val, _) {
    this.props.selectChange(val);
  }

  render() {
    const hide = this.props.hidden;
    if (hide) {
      return null;
    } else {
      return (
        <FormGroup label={this.props.labelName} fieldId="ansible-select">
          <Select value={this.props.selected} onChange={this.onSelectChange} aria-label="Select Input">
            {this.props.data.map((env, index) => (
              <SelectOption isDisabled={env.disabled} key={index} value={env} label={env} />
            ))}
          </Select>
        </FormGroup>
      );
    }
  }
}

export default AnsibleSelect;
