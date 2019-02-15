import React from 'react';
import PropTypes from 'prop-types';

class Tooltip extends React.Component {
  transforms = {
    top: {
      bottom: '100%',
      left: '50%',
      transform: 'translate(-50%, -25%)'
    },
    bottom: {
      top: '100%',
      left: '50%',
      transform: 'translate(-50%, 25%)'
    },
    left: {
      top: '50%',
      right: '100%',
      transform: 'translate(-25%, -50%)'
    },
    right: {
      bottom: '100%',
      left: '50%',
      transform: 'translate(25%, 50%)'
    },
  };

  constructor (props) {
    super(props);

    this.state = {
      isDisplayed: false
    };
  }

  render () {
    const {
      children,
      message,
      position,
    } = this.props;
    const {
      isDisplayed
    } = this.state;

    return (
      <span
        style={{ position: 'relative' }}
        className="mouseOutHandler"
        onMouseLeave={() => this.setState({ isDisplayed: false })}
        onBlur={() => this.setState({ isDisplayed: false })}
      >
        { isDisplayed
          && (
            <div
              style={{ position: 'absolute', zIndex: '10', ...this.transforms[position] }}
              className={`pf-c-tooltip pf-m-${position}`}
            >
              <div className="pf-c-tooltip__arrow" />
              <div className="pf-c-tooltip__content">
                { message }
              </div>
            </div>
          )
        }
        <span
          className="mouseOverHandler"
          onMouseOver={() => this.setState({ isDisplayed: true })}
          onFocus={() => this.setState({ isDisplayed: true })}
        >
          { children }
        </span>
      </span>
    );
  }
}

Tooltip.propTypes = {
  children: PropTypes.element.isRequired,
  message: PropTypes.string.isRequired,
  position: PropTypes.string,
};

Tooltip.defaultProps = {
  position: 'top',
};

export default Tooltip;
