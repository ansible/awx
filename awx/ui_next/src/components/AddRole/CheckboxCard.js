import React, { Component, Fragment } from 'react';
import PropTypes from 'prop-types';
import { Checkbox as PFCheckbox } from '@patternfly/react-core';
import styled from 'styled-components';

const CheckboxWrapper = styled.div`
  display: flex;
  border: 1px solid var(--pf-global--BorderColor--200);
  border-radius: var(--pf-global--BorderRadius--sm);
  padding: 10px;
`;

const Checkbox = styled(PFCheckbox)`
  width: 100%;
  & label {
    width: 100%;
  }
`;

class CheckboxCard extends Component {
  render() {
    const { name, description, isSelected, onSelect, itemId } = this.props;
    return (
      <CheckboxWrapper>
        <Checkbox
          isChecked={isSelected}
          onChange={onSelect}
          aria-label={name}
          id={`checkbox-card-${itemId}`}
          label={
            <Fragment>
              <div style={{ fontWeight: 'bold' }}>{name}</div>
              <div>{description}</div>
            </Fragment>
          }
          value={itemId}
        />
      </CheckboxWrapper>
    );
  }
}

CheckboxCard.propTypes = {
  name: PropTypes.string.isRequired,
  description: PropTypes.string,
  isSelected: PropTypes.bool,
  onSelect: PropTypes.func,
  itemId: PropTypes.number.isRequired,
};

CheckboxCard.defaultProps = {
  description: '',
  isSelected: false,
  onSelect: null,
};

export default CheckboxCard;
