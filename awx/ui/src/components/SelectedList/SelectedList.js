import React from 'react';
import PropTypes from 'prop-types';
import { Chip, Split as PFSplit, SplitItem } from '@patternfly/react-core';

import styled from 'styled-components';
import ChipGroup from '../ChipGroup';

const Split = styled(PFSplit)`
  margin: 20px 0 5px 0 !important;
  align-items: baseline;
`;

const SplitLabelItem = styled(SplitItem)`
  font-weight: bold;
  margin-right: 32px;
  word-break: initial;
`;

function SelectedList(props) {
  const { label, selected, onRemove, displayKey, isReadOnly, renderItemChip } =
    props;

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
        <ChipGroup
          numChips={5}
          totalChips={selected.length}
          ouiaId="selected-list-chips"
        >
          {selected.map((item) =>
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
