import React from 'react';

import {
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
    const { value, data } = this.props;
    let elem;
    if (count > 1) {
      elem = (
        <Select value={value} onChange={this.onSelectChange} aria-label="Select Input">
          {data.map((datum) => (
            <SelectOption isDisabled={datum.disabled} key={datum} value={datum} label={datum} />
          ))}
        </Select>
      );
    } else {
      elem = null;
    }

    return elem;
  }
}

export default AnsibleSelect;
