import React from 'react';
import { string, func } from 'prop-types';
import { Link } from 'react-router-dom';
import { Button as PFButton, Tooltip } from '@patternfly/react-core';
import { PlusIcon } from '@patternfly/react-icons';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';

const Button = styled(PFButton)`
  && {
    background-color: #5cb85c;
    padding: 5px 8px;
    --pf-global--FontSize--md: 14px;
  }
`;

function ToolbarAddButton({ linkTo, onClick, i18n }) {
  if (!linkTo && !onClick) {
    throw new Error(
      'ToolbarAddButton requires either `linkTo` or `onClick` prop'
    );
  }
  if (linkTo) {
    return (
      <Tooltip content={i18n._(t`Add`)} position="top">
        <Button
          component={Link}
          to={linkTo}
          variant="primary"
          aria-label={i18n._(t`Add`)}
        >
          <PlusIcon />
        </Button>
      </Tooltip>
    );
  }
  return (
    <Button variant="primary" aria-label={i18n._(t`Add`)} onClick={onClick}>
      <PlusIcon />
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
