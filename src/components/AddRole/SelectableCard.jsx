import React, { Component } from 'react';
import PropTypes from 'prop-types';

class SelectableCard extends Component {
  render () {
    const {
      label,
      onClick,
      isSelected
    } = this.props;
    return (
      <div
        className={isSelected ? 'awx-selectableCard awx-selectableCard__selected' : 'awx-selectableCard'}
        onClick={onClick}
        onKeyPress={onClick}
        role="button"
        tabIndex="0"
      >
        <div
          className="awx-selectableCard__indicator"
        />
        <div className="awx-selectableCard__label">{label}</div>
      </div>
    );
  }
}

SelectableCard.propTypes = {
  label: PropTypes.string,
  onClick: PropTypes.func.isRequired,
  isSelected: PropTypes.bool
};

SelectableCard.defaultProps = {
  label: '',
  isSelected: false
};

export default SelectableCard;
