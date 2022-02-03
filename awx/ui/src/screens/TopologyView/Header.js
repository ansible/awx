import React from 'react';
import PropTypes from 'prop-types';

import { t } from '@lingui/macro';
import {
  PageSection,
  PageSectionVariants,
  Switch,
  Title,
  Tooltip,
} from '@patternfly/react-core';

const Header = ({ title, handleSwitchToggle, toggleState }) => {
  const { light } = PageSectionVariants;

  return (
    <PageSection variant={light}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div
          style={{
            minHeight: '31px',
          }}
        >
          <Title size="2xl" headingLevel="h2" data-cy="screen-title">
            {title}
          </Title>
        </div>
        <div>
          <Tooltip content={t`Toggle legend`} position="top">
            <Switch
              id="legend-toggle-switch"
              label={t`Legend`}
              isChecked={toggleState}
              onChange={() => handleSwitchToggle(!toggleState)}
            />
          </Tooltip>
        </div>
      </div>
    </PageSection>
  );
};

Header.propTypes = {
  title: PropTypes.string.isRequired,
};

export default Header;
