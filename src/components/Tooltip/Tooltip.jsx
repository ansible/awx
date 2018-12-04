import React from 'react';

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
        onMouseLeave={() => this.setState({ isDisplayed: false })}
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
          onMouseOver={() => this.setState({ isDisplayed: true })}
          onFocus={() => this.setState({ isDisplayed: true })}
        >
          { children }
        </span>
      </span>
    );
  }
}

export default Tooltip;
