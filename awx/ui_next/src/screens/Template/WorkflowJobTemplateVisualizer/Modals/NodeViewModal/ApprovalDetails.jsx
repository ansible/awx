import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { DetailList, Detail } from '@components/DetailList';

function ApprovalDetails({ i18n, node }) {
  const { name, description, timeout } = node.unifiedJobTemplate;

  let timeoutValue = i18n._(t`None`);

  if (timeout) {
    const minutes = Math.floor(timeout / 60);
    const seconds = timeout - minutes * 60;
    timeoutValue = i18n._(t`${minutes}min ${seconds}sec`);
  }
  return (
    <DetailList gutter="sm">
      <Detail label={i18n._(t`Node Type`)} value={i18n._(t`Approval`)} />
      <Detail label={i18n._(t`Name`)} value={name} />
      <Detail label={i18n._(t`Description`)} value={description} />
      <Detail label={i18n._(t`Timeout`)} value={timeoutValue} />
    </DetailList>
  );
}

export default withI18n()(ApprovalDetails);
