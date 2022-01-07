import React, { useState } from 'react';

import { t } from '@lingui/macro';
import { Button, Modal } from '@patternfly/react-core';
import { SearchPlusIcon } from '@patternfly/react-icons';

import { formatDateString } from 'util/dates';

import { DetailList, Detail } from 'components/DetailList';
import { VariablesDetail } from 'components/CodeEditor';

function ActivityStreamDetailButton({ streamItem, user, description }) {
  const [isOpen, setIsOpen] = useState(false);

  const setting = streamItem?.summary_fields?.setting;
  const changeRows = Math.max(
    Object.keys(streamItem?.changes || []).length + 2,
    6
  );

  return (
    <>
      <Button
        ouiaId={`${streamItem.id}-view-details-button`}
        aria-label={t`View event details`}
        variant="plain"
        component="button"
        onClick={() => setIsOpen(true)}
      >
        <SearchPlusIcon />
      </Button>
      <Modal
        variant="large"
        isOpen={isOpen}
        title={t`Event detail`}
        aria-label={t`Event detail modal`}
        onClose={() => setIsOpen(false)}
      >
        <DetailList gutter="sm">
          <Detail
            label={t`Time`}
            value={formatDateString(streamItem.timestamp)}
          />
          <Detail label={t`Initiated by`} value={user} />
          <Detail
            label={t`Setting category`}
            value={setting && setting[0]?.category}
          />
          <Detail label={t`Setting name`} value={setting && setting[0]?.name} />
          <Detail fullWidth label={t`Action`} value={description} />
          {streamItem?.changes && (
            <VariablesDetail
              label={t`Changes`}
              rows={changeRows}
              value={
                streamItem?.changes ? JSON.stringify(streamItem.changes) : ''
              }
              name="changes"
              dataCy="activity-stream-detail-changes"
            />
          )}
        </DetailList>
      </Modal>
    </>
  );
}

export default ActivityStreamDetailButton;
