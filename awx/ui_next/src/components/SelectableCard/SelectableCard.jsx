import React from 'react';
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
  display: flex;
  cursor: pointer;
`;

const Indicator = styled.div`
  display: flex;
  flex: 0 0 5px;
  background-color: ${props =>
    props.isSelected ? 'var(--pf-global--active-color--100)' : null};
`;

const Contents = styled.div`
  padding: 10px 20px;
`;

const Description = styled.p`
  font-size: 14px;
`;

function SelectableCard({ label, description, onClick, isSelected, dataCy }) {
  return (
    <SelectableItem
      onClick={onClick}
      onKeyPress={onClick}
      role="button"
      tabIndex="0"
      data-cy={dataCy}
      isSelected={isSelected}
    >
      <Indicator isSelected={isSelected} />
      <Contents>
        <b>{label}</b>
        <Description>{description}</Description>
      </Contents>
    </SelectableItem>
  );
}

SelectableCard.propTypes = {
  label: PropTypes.string,
  description: PropTypes.string,
  onClick: PropTypes.func.isRequired,
  isSelected: PropTypes.bool,
};

SelectableCard.defaultProps = {
  label: '',
  description: '',
  isSelected: false,
};

export default SelectableCard;
