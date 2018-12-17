import React from 'react';
import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';

import {
  Button,
  ButtonVariant
} from '@patternfly/react-core';

import { UserIcon } from '@patternfly/react-icons';

const LogoutButton = ({ onDevLogout }) => (
  <I18n>
    {({ i18n }) => (
      <Button
        id="button-logout"
        aria-label={i18n._(t`Logout`)}
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
    )}
  </I18n>
);

export default LogoutButton;
