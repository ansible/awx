import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { Chip, Split as PFSplit, SplitItem } from '@patternfly/react-core';

import styled from 'styled-components';
import ChipGroup from '../ChipGroup';

const Split = styled(PFSplit)`
  margin: 20px 0px;
  align-items: baseline;
`;

const SplitLabelItem = styled(SplitItem)`
  font-weight: bold;
  margin-right: 32px;
  word-break: initial;
`;

class SelectedList extends Component {
  render() {
    const {
      label,
      selected,
      onRemove,
      displayKey,
      isReadOnly,
      renderItemChip,
    } = this.props;

    const renderChip =
      renderItemChip ||
      (({ item, removeItem }) => (
        <Chip key={item.id} onClick={removeItem} isReadOnly={isReadOnly}>
          {item[displayKey]}
        </Chip>
      ));

    return (
      <Split>
        <SplitLabelItem>{label}</SplitLabelItem>
        <SplitItem>
          <ChipGroup numChips={5} totalChips={selected.length}>
            {selected.map(item =>
              renderChip({
                item,
                removeItem: () => onRemove(item),
                canDelete: !isReadOnly,
              })
            )}
          </ChipGroup>
        </SplitItem>
      </Split>
    );
  }
}

SelectedList.propTypes = {
  displayKey: PropTypes.string,
  label: PropTypes.string,
  onRemove: PropTypes.func,
  selected: PropTypes.arrayOf(PropTypes.object).isRequired,
  isReadOnly: PropTypes.bool,
  renderItemChip: PropTypes.func,
};

SelectedList.defaultProps = {
  displayKey: 'name',
  label: 'Selected',
  onRemove: () => null,
  isReadOnly: false,
  renderItemChip: null,
};

export default SelectedList;
