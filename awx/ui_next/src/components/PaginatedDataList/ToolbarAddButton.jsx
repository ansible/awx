import React from 'react';
import { string, func } from 'prop-types';
import { Link } from 'react-router-dom';
import { Button, DropdownItem, Tooltip } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useKebabifiedMenu } from '../../contexts/Kebabified';

function ToolbarAddButton({ linkTo, onClick, i18n, isDisabled }) {
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
        component={linkTo ? Link : Button}
        to={linkTo}
        onClick={!onClick ? undefined : onClick}
      >
        {i18n._(t`Add`)}
      </DropdownItem>
    );
  }
  if (linkTo) {
    return (
      <Tooltip content={i18n._(t`Add`)} position="top">
        <Button
          isDisabled={isDisabled}
          component={Link}
          to={linkTo}
          variant="primary"
          aria-label={i18n._(t`Add`)}
        >
          {i18n._(t`Add`)}
        </Button>
      </Tooltip>
    );
  }
  return (
    <Button variant="primary" aria-label={i18n._(t`Add`)} onClick={onClick}>
      {i18n._(t`Add`)}
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
