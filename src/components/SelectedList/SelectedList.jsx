import React, { Component } from 'react';
import {
  Chip
} from '@patternfly/react-core';

class SelectedList extends Component {
  constructor (props) {
    super(props);

    this.state = {
      showOverflow: false
    };

    this.showOverflow = this.showOverflow.bind(this);
  }

  showOverflow = () => {
    this.setState({ showOverflow: true });
  };

  render () {
    const { label, selected, showOverflowAfter, onRemove } = this.props;
    const { showOverflow } = this.state;
    return (
      <div className="awx-selectedList">
        <div className="pf-l-split">
          <div className="pf-l-split__item pf-u-align-items-center">
            {label}
          </div>
          <div className="pf-l-split__item">
            <div className="pf-c-chip-group">
              {selected
                .slice(0, showOverflow ? selected.length : showOverflowAfter)
                .map(selectedItem => (
                  <Chip
                    key={selectedItem.id}
                    onClick={() => onRemove(selectedItem)}
                  >
                    {selectedItem.name}
                  </Chip>
                ))}
              {(
                !showOverflow
                && selected.length > showOverflowAfter
              ) && (
                <Chip
                  isOverflowChip
                  onClick={() => this.showOverflow()}
                >
                  {`${(selected.length - showOverflowAfter).toString()} more`}
                </Chip>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default SelectedList;
