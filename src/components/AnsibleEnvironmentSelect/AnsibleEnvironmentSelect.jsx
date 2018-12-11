import React from 'react';
import {
  FormGroup,
  Select,
  SelectOption,
} from '@patternfly/react-core';
import { API_CONFIG } from '../../endpoints';
import api from '../../api';

class AnsibleEnvironmentSelect extends React.Component {
  constructor(props) {
    super(props);
    this.onSelectChange = this.onSelectChange.bind(this);
  }

  state = {
    custom_virtualenvs: [],
    isHidden: true,
  }

  async componentDidMount() {
    const { data } = await api.get(API_CONFIG);
    this.setState({ custom_virtualenvs: [...data.custom_virtualenvs] });
    if (this.state.custom_virtualenvs.length > 1) {
      // Show dropdown if we have more than one ansible environment
      this.setState({ isHidden: !this.state.isHidden });
    }
  }

  onSelectChange(val, _) {
    this.props.selectChange(val);
  }

  render() {
    const { isHidden } = this.state;
    if (isHidden) {
      return null;
    } else {
      return (
        <FormGroup label="Ansible Environment" fieldId="simple-form-instance-groups">
          <Select value={this.props.selected} onChange={this.onSelectChange} aria-label="Select Input">
            <SelectOption isDisabled value="Select Ansible Environment" label="Select Ansible Environment" />
            {this.state.custom_virtualenvs.map((env, index) => (
              <SelectOption isDisabled={env.disabled} key={index} value={env} label={env} />
            ))}
          </Select>
        </FormGroup>
      );
    }
  }
}

export default AnsibleEnvironmentSelect;
