import React from 'react';

import {
  Button,
  ButtonVariant
} from '@patternfly/react-core';

import { UserIcon } from '@patternfly/react-icons';

const LogoutButton = ({ onDevLogout }) => (
  <Button
    id="button-logout"
    aria-label="Logout"
    variant={ButtonVariant.plain}
    onClick={onDevLogout}
    onKeyDown={event => {
      if (event.keyCode === 13) {
        onDevLogout();
      }
    }}
  >
    <UserIcon />
  </Button>
);

export default LogoutButton;
