import React, { Component } from 'react';
import PropTypes from 'prop-types';
import {
  Chip
} from '@patternfly/react-core';

import VerticalSeparator from '../VerticalSeparator';

const selectedRowStyling = {
  paddingTop: '15px',
  paddingBottom: '5px',
  borderLeft: '0',
  borderRight: '0'
};

const selectedLabelStyling = {
  alignSelf: 'center',
  fontSize: '14px',
  fontWeight: 'bold'
};

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
        <div className="pf-l-split" style={selectedRowStyling}>
          <div className="pf-l-split__item" style={selectedLabelStyling}>
            {label}
          </div>
          <VerticalSeparator />
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

SelectedList.propTypes = {
  label: PropTypes.string,
  onRemove: PropTypes.func.isRequired,
  selected: PropTypes.arrayOf(PropTypes.object).isRequired,
  showOverflowAfter: PropTypes.number,
};

SelectedList.defaultProps = {
  label: 'Selected',
  showOverflowAfter: 5,
};

export default SelectedList;
