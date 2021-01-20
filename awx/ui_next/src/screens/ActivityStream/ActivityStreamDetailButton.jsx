import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button, Modal } from '@patternfly/react-core';
import { SearchPlusIcon } from '@patternfly/react-icons';

import { formatDateString } from '../../util/dates';

import { DetailList, Detail } from '../../components/DetailList';
import { VariablesDetail } from '../../components/CodeMirrorInput';

function ActivityStreamDetailButton({ i18n, streamItem, user, description }) {
  const [isOpen, setIsOpen] = useState(false);

  const setting = streamItem?.summary_fields?.setting;
  const changeRows = Math.max(
    Object.keys(streamItem?.changes || []).length + 2,
    6
  );

  return (
    <>
      <Button
        aria-label={i18n._(t`View event details`)}
        variant="plain"
        component="button"
        onClick={() => setIsOpen(true)}
      >
        <SearchPlusIcon />
      </Button>
      <Modal
        variant="large"
        isOpen={isOpen}
        title={i18n._(t`Event detail`)}
        aria-label={i18n._(t`Event detail modal`)}
        onClose={() => setIsOpen(false)}
      >
        <DetailList gutter="sm">
          <Detail
            label={i18n._(t`Time`)}
            value={formatDateString(streamItem.timestamp)}
          />
          <Detail label={i18n._(t`Initiated by`)} value={user} />
          <Detail
            label={i18n._(t`Setting category`)}
            value={setting && setting[0]?.category}
          />
          <Detail
            label={i18n._(t`Setting name`)}
            value={setting && setting[0]?.name}
          />
          <Detail fullWidth label={i18n._(t`Action`)} value={description} />
          {streamItem?.changes && (
            <VariablesDetail
              label={i18n._(t`Changes`)}
              rows={changeRows}
              value={streamItem?.changes}
            />
          )}
        </DetailList>
      </Modal>
    </>
  );
}

export default withI18n()(ActivityStreamDetailButton);
