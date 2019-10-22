import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { Split as PFSplit, SplitItem } from '@patternfly/react-core';
import styled from 'styled-components';
import { ChipGroup, Chip, CredentialChip } from '../Chip';
import VerticalSeparator from '../VerticalSeparator';

const Split = styled(PFSplit)`
  padding-top: 15px;
  padding-bottom: 5px;
  border-bottom: #ebebeb var(--pf-global--BorderWidth--sm) solid;
  align-items: baseline;
`;

const SplitLabelItem = styled(SplitItem)`
  font-size: 14px;
  font-weight: bold;
  word-break: initial;
`;

class SelectedList extends Component {
  render() {
    const {
      label,
      selected,
      showOverflowAfter,
      onRemove,
      displayKey,
      isReadOnly,
      isCredentialList,
    } = this.props;
    const chips = isCredentialList
      ? selected.map(item => (
          <CredentialChip
            key={item.id}
            isReadOnly={isReadOnly}
            onClick={() => onRemove(item)}
            credential={item}
          >
            {item[displayKey]}
          </CredentialChip>
        ))
      : selected.map(item => (
          <Chip
            key={item.id}
            isReadOnly={isReadOnly}
            onClick={() => onRemove(item)}
          >
            {item[displayKey]}
          </Chip>
        ));
    return (
      <Split>
        <SplitLabelItem>{label}</SplitLabelItem>
        <VerticalSeparator />
        <SplitItem>
          <ChipGroup showOverflowAfter={showOverflowAfter}>{chips}</ChipGroup>
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
  showOverflowAfter: PropTypes.number,
  isReadOnly: PropTypes.bool,
};

SelectedList.defaultProps = {
  displayKey: 'name',
  label: 'Selected',
  onRemove: () => null,
  showOverflowAfter: 5,
  isReadOnly: false,
};

export default SelectedList;
