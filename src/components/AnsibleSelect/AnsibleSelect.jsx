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

  onSelectChange (val) {
    const { selectChange } = this.props;
    selectChange(val);
  }

  render () {
    const { count } = this.state;
    const { labelName, selected, data, defaultSelected } = this.props;
    let elem;
    if (count > 1) {
      elem = (
        <FormGroup label={labelName} fieldId="ansible-select">
          <Select value={selected} onChange={this.onSelectChange} aria-label="Select Input">
            <SelectOption isDisabled key="" value="" label={`Use Default ${labelName}`} />
            {data.map((datum) =>
              datum !== defaultSelected ?
              (<SelectOption key={datum} value={datum} label={datum} />) : null)
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

export default AnsibleSelect;
