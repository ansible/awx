import React, { useState } from 'react';
import { shape } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { formatDateString, formatDateStringUTC } from '@util/dates';
import { Split, SplitItem, TextListItemVariants } from '@patternfly/react-core';
import { DetailName, DetailValue } from '@components/DetailList';
import MultiButtonToggle from '@components/MultiButtonToggle';

function ScheduleOccurrences({ preview = { local: [], utc: [] }, i18n }) {
  const [mode, setMode] = useState('local');

  if (preview.local.length < 2) {
    return null;
  }

  return (
    <>
      <DetailName
        component={TextListItemVariants.dt}
        fullWidth
        css="grid-column: 1 / -1"
      >
        <Split gutter="sm">
          <SplitItem>
            <div className="pf-c-form__label">
              <span
                className="pf-c-form__label-text"
                css="font-weight: var(--pf-global--FontWeight--bold)"
              >
                {i18n._(t`Occurrences`)}
              </span>
              <span css="margin-left: 10px">
                {i18n._(t`(Limited to first 10)`)}
              </span>
            </div>
          </SplitItem>
          <SplitItem>
            <MultiButtonToggle
              buttons={[['local', 'Local'], ['utc', 'UTC']]}
              value={mode}
              onChange={newMode => setMode(newMode)}
            />
          </SplitItem>
        </Split>
      </DetailName>
      <DetailValue
        component={TextListItemVariants.dd}
        fullWidth
        css="grid-column: 1 / -1; margin-top: -10px"
      >
        {preview[mode].map(dateStr => (
          <div key={dateStr}>
            {mode === 'local'
              ? formatDateString(dateStr)
              : formatDateStringUTC(dateStr)}
          </div>
        ))}
      </DetailValue>
    </>
  );
}

ScheduleOccurrences.propTypes = {
  preview: shape(),
};

ScheduleOccurrences.defaultProps = {
  preview: { local: [], utc: [] },
};

export default withI18n()(ScheduleOccurrences);
