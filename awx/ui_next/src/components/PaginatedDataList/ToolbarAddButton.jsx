import React from 'react';
import { string, func } from 'prop-types';
import { Link } from 'react-router-dom';
import { Button, DropdownItem, Tooltip } from '@patternfly/react-core';
import CaretDownIcon from '@patternfly/react-icons/dist/js/icons/caret-down-icon';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useKebabifiedMenu } from '../../contexts/Kebabified';

function ToolbarAddButton({
  linkTo,
  onClick,
  i18n,
  isDisabled,
  defaultLabel = i18n._(t`Add`),
  showToggleIndicator,
}) {
  const { isKebabified } = useKebabifiedMenu();

  if (!linkTo && !onClick) {
    throw new Error(
      'ToolbarAddButton requires either `linkTo` or `onClick` prop'
    );
  }

  if (isKebabified) {
    return (
      <DropdownItem
        key="add"
        isDisabled={isDisabled}
        component={linkTo ? Link : 'button'}
        to={linkTo}
        onClick={!onClick ? undefined : onClick}
      >
        {defaultLabel}
      </DropdownItem>
    );
  }
  if (linkTo) {
    return (
      <Tooltip content={defaultLabel} position="top">
        <Button
          isDisabled={isDisabled}
          component={Link}
          to={linkTo}
          variant="primary"
          aria-label={defaultLabel}
        >
          {defaultLabel}
        </Button>
      </Tooltip>
    );
  }
  return (
    <Button
      icon={showToggleIndicator ? <CaretDownIcon /> : null}
      iconPosition={showToggleIndicator ? 'right' : null}
      variant="primary"
      aria-label={defaultLabel}
      onClick={onClick}
    >
      {defaultLabel}
    </Button>
  );
}
ToolbarAddButton.propTypes = {
  linkTo: string,
  onClick: func,
};
ToolbarAddButton.defaultProps = {
  linkTo: null,
  onClick: null,
};

export default withI18n()(ToolbarAddButton);
