import React from 'react';
import { string, func } from 'prop-types';
import { Link } from 'react-router-dom';
import { Button as PFButton } from '@patternfly/react-core';
import { PlusIcon } from '@patternfly/react-icons';
import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';

const Button = styled(PFButton)`
  &&& { /* higher specificity order */
    background-color: #5cb85c;
    min-width: 0;
    width: 30px;
    height: 30px;
    text-align: center;
    padding: 0;
    margin: 0;
    margin-right: 20px;
  }
`;

function ToolbarAddButton ({ linkTo, onClick }) {
  if (!linkTo && !onClick) {
    throw new Error('ToolbarAddButton requires either `linkTo` or `onClick` prop');
  }
  if (linkTo) {
    // TODO: This should only be a <Link> (no <Button>) but CSS is off
    return (
      <I18n>
        {({ i18n }) => (
          <Link to={linkTo}>
            <Button
              variant="primary"
              aria-label={i18n._(t`Add`)}
            >
              <PlusIcon />
            </Button>
          </Link>
        )}
      </I18n>
    );
  }
  return (
    <I18n>
      {({ i18n }) => (
        <Button
          variant="primary"
          aria-label={i18n._(t`Add`)}
          onClick={onClick}
        >
          <PlusIcon />
        </Button>
      )}
    </I18n>
  );
}
ToolbarAddButton.propTypes = {
  linkTo: string,
  onClick: func,
};
ToolbarAddButton.defaultProps = {
  linkTo: null,
  onClick: null
};

export default ToolbarAddButton;
