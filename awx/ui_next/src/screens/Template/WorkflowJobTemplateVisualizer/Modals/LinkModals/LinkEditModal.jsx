import React, { useContext } from 'react';
import { Title } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { WorkflowDispatchContext } from '../../../../../contexts/Workflow';
import LinkModal from './LinkModal';

function LinkEditModal({ i18n }) {
  const dispatch = useContext(WorkflowDispatchContext);
  return (
    <LinkModal
      header={
        <Title headingLevel="h1" size="xl">
          {i18n._(t`Edit Link`)}
        </Title>
      }
      onConfirm={linkType => dispatch({ type: 'UPDATE_LINK', linkType })}
    />
  );
}

export default withI18n()(LinkEditModal);
