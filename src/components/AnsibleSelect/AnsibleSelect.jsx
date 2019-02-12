import React from 'react';

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
    const { onChange } = this.props;
    onChange(val, event);
  }

  render () {
    const { count } = this.state;
    const { labelName, selected, data, fieldId } = this.props;
    let elem;
    if (count > 1) {
      elem = (
        <FormGroup label={labelName} fieldId={fieldId || 'ansible-select'}>
          <Select value={selected} id={`select-${fieldId}` || 'ansible-select-element'} onChange={this.onSelectChange} aria-label="Select Input">
            {data.map((datum) => (
              <SelectOption isDisabled={datum.disabled} key={datum} value={datum} label={datum} />
            ))}
          </Select>
        </FormGroup>
      );
    } else {
      elem = null;
    }

    return elem;
  }
}

export default AnsibleSelect;
