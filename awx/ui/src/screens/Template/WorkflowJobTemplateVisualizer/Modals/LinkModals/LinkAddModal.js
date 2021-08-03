import React, { useContext } from 'react';
import { Title } from '@patternfly/react-core';

import { t } from '@lingui/macro';
import { WorkflowDispatchContext } from 'contexts/Workflow';
import LinkModal from './LinkModal';

function LinkAddModal() {
  const dispatch = useContext(WorkflowDispatchContext);
  return (
    <LinkModal
      header={
        <Title headingLevel="h1" size="xl">
          {t`Add Link`}
        </Title>
      }
      onConfirm={(linkType) => dispatch({ type: 'CREATE_LINK', linkType })}
    />
  );
}

export default LinkAddModal;
