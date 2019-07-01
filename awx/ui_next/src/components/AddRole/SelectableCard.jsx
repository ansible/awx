import React, { Component } from 'react';
import PropTypes from 'prop-types';
import styled from 'styled-components';

const SelectableItem = styled.div`
  min-width: 200px;
  border: 1px solid var(--pf-global--BorderColor--200);
  border-radius: var(--pf-global--BorderRadius--sm);
  border: 1px solid;
  border-color: ${props =>
    props.isSelected
      ? 'var(--pf-global--active-color--100)'
      : 'var(--pf-global--BorderColor--200)'};
  margin-right: 20px;
  font-weight: bold;
  display: flex;
  cursor: pointer;
`;

const Indicator = styled.div`
  display: flex;
  flex: 0 0 5px;
  background-color: ${props =>
    props.isSelected ? 'var(--pf-global--active-color--100)' : null};
`;

const Label = styled.div`
  display: flex;
  flex: 1;
  align-items: center;
  padding: 20px;
`;

class SelectableCard extends Component {
  render() {
    const { label, onClick, isSelected } = this.props;

    return (
      <SelectableItem
        onClick={onClick}
        onKeyPress={onClick}
        role="button"
        tabIndex="0"
        isSelected={isSelected}
      >
        <Indicator isSelected={isSelected} />
        <Label>{label}</Label>
      </SelectableItem>
    );
  }
}

SelectableCard.propTypes = {
  label: PropTypes.string,
  onClick: PropTypes.func.isRequired,
  isSelected: PropTypes.bool,
};

SelectableCard.defaultProps = {
  label: '',
  isSelected: false,
};

export default SelectableCard;
