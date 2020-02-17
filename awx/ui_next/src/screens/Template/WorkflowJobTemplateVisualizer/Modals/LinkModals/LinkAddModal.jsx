import React, { useContext } from 'react';
import { WorkflowDispatchContext } from '@contexts/Workflow';
import { BaseSizes, Title, TitleLevel } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import LinkModal from './LinkModal';

function LinkAddModal({ i18n }) {
  const dispatch = useContext(WorkflowDispatchContext);
  return (
    <LinkModal
      header={
        <Title headingLevel={TitleLevel.h1} size={BaseSizes['2xl']}>
          {i18n._(t`Add Link`)}
        </Title>
      }
      onConfirm={linkType => dispatch({ type: 'CREATE_LINK', linkType })}
    />
  );
}

export default withI18n()(LinkAddModal);
