import React from 'react';
import PropTypes from 'prop-types';

import { t } from '@lingui/macro';
import {
  Button,
  PageSection,
  PageSectionVariants,
  Switch,
  Title,
  Tooltip,
} from '@patternfly/react-core';

import {
  SearchMinusIcon,
  SearchPlusIcon,
  ExpandArrowsAltIcon,
} from '@patternfly/react-icons';

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
          <Tooltip content={t`Zoom in`} position="top">
            <Button
              ouiaId="zoom-in-button"
              aria-label={t`Zoom in`}
              variant="plain"
              icon={<SearchPlusIcon />}
            >
              <SearchPlusIcon />
            </Button>
          </Tooltip>
          <Tooltip content={t`Zoom out`} position="top">
            <Button
              ouiaId="zoom-out-button"
              aria-label={t`Zoom out`}
              variant="plain"
              icon={<SearchMinusIcon />}
            >
              <SearchMinusIcon />
            </Button>
          </Tooltip>
          <Tooltip content={t`Fit to screen`} position="top">
            <Button
              ouiaId="fit-to-screen-button"
              aria-label={t`Fit to screen`}
              variant="plain"
              icon={<ExpandArrowsAltIcon />}
            >
              <ExpandArrowsAltIcon />
            </Button>
          </Tooltip>
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
