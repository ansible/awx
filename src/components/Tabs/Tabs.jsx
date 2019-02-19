import React from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import { Button } from '@patternfly/react-core';
import { TimesIcon } from '@patternfly/react-icons';
import Tooltip from '../Tooltip';
import './tabs.scss';

const Tabs = ({ children, labelText, closeButton }) => (
  <div
    aria-label={labelText}
    className="pf-c-tabs pf-u-flex-direction-row pf-u-justify-content-space-between"
  >
    <ul className="pf-c-tabs__list">
      {children}
    </ul>
    {closeButton
      && (
        <div className="pf-u-align-self-center">
          <Tooltip
            message={closeButton.text}
            position="top"
          >
            <Link to={closeButton.link}>
              <Button
                variant="plain"
                aria-label={closeButton.text}
              >
                <TimesIcon />
              </Button>
            </Link>
          </Tooltip>
        </div>
      )
    }
  </div>
);

Tabs.propTypes = {
  children: PropTypes.oneOfType([
    PropTypes.arrayOf(PropTypes.node),
    PropTypes.node
  ]).isRequired,
  labelText: PropTypes.string,
  closeButton: PropTypes.shape({
    text: PropTypes.string,
    link: PropTypes.string,
  }),
};

Tabs.defaultProps = {
  labelText: null,
  closeButton: null,
};

export default Tabs;
