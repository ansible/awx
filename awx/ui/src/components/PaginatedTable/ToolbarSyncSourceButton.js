import React from 'react';
import { func } from 'prop-types';
import { Button, DropdownItem, Tooltip } from '@patternfly/react-core';

import { t } from '@lingui/macro';
import { useKebabifiedMenu } from 'contexts/Kebabified';

function ToolbarSyncSourceButton({ onClick }) {
  const { isKebabified } = useKebabifiedMenu();

  if (isKebabified) {
    return (
      <DropdownItem
        ouiaId="sync-all-button"
        key="add"
        component="button"
        onClick={onClick}
      >
        {t`Sync all`}
      </DropdownItem>
    );
  }

  return (
    <Tooltip key="update" content={t`Sync all sources`} position="top">
      <Button
        ouiaId="sync-all-button"
        onClick={onClick}
        aria-label={t`Sync all`}
        variant="secondary"
      >
        {t`Sync all`}
      </Button>
    </Tooltip>
  );
}

ToolbarSyncSourceButton.propTypes = {
  onClick: func,
};
ToolbarSyncSourceButton.defaultProps = {
  onClick: null,
};

export default ToolbarSyncSourceButton;
