import React, { Component, Fragment } from 'react';
import PropTypes from 'prop-types';
import {
  Chip
} from '@patternfly/react-core';

import BasicChip from '../BasicChip/BasicChip';
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
    const {
      label,
      selected,
      showOverflowAfter,
      onRemove,
      displayKey,
      isReadOnly
    } = this.props;
    const { showOverflow } = this.state;
    const visibleItems = selected.slice(0, showOverflow ? selected.length : showOverflowAfter);
    return (
      <div className="awx-selectedList">
        <div className="pf-l-split" style={selectedRowStyling}>
          <div className="pf-l-split__item" style={selectedLabelStyling}>
            {label}
          </div>
          <VerticalSeparator />
          <div className="pf-l-split__item">
            <div className="pf-c-chip-group">
              {isReadOnly ? (
                <Fragment>
                  {visibleItems
                    .map(selectedItem => (
                      <BasicChip
                        key={selectedItem.id}
                      >
                        {selectedItem[displayKey]}
                      </BasicChip>
                    ))
                  }
                </Fragment>
              ) : (
                <Fragment>
                  {visibleItems
                    .map(selectedItem => (
                      <Chip
                        key={selectedItem.id}
                        onClick={() => onRemove(selectedItem)}
                      >
                        {selectedItem[displayKey]}
                      </Chip>
                    ))
                  }
                </Fragment>
              )}
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
  displayKey: PropTypes.string,
  label: PropTypes.string,
  onRemove: PropTypes.func,
  selected: PropTypes.arrayOf(PropTypes.object).isRequired,
  showOverflowAfter: PropTypes.number,
  isReadOnly: PropTypes.bool
};

SelectedList.defaultProps = {
  displayKey: 'name',
  label: 'Selected',
  onRemove: () => null,
  showOverflowAfter: 5,
  isReadOnly: false
};

export default SelectedList;
