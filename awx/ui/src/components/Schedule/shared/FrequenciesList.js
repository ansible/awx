import React, { useState } from 'react';
import { t } from '@lingui/macro';
import {
  Button,
  Switch,
  Toolbar,
  ToolbarContent,
  ToolbarItem,
} from '@patternfly/react-core';
import { PencilAltIcon } from '@patternfly/react-icons';
import {
  TableComposable,
  Tbody,
  Thead,
  Th,
  Tr,
  Td,
} from '@patternfly/react-table';

import { useField } from 'formik';
import ContentEmpty from 'components/ContentEmpty';

function FrequenciesList({ openWizard }) {
  const [isShowingRules, setIsShowingRules] = useState(true);
  const [frequencies] = useField('frequencies');
  const list = (freq) => (
    <Tr key={freq.rrule}>
      <Td>{freq.frequency}</Td>
      <Td>{freq.rrule}</Td>
      <Td>{t`End`}</Td>
      <Td>
        <Button
          variant="plain"
          aria-label={t`Click to toggle default value`}
          ouiaId={freq ? `${freq}-button` : 'new-freq-button'}
          onClick={() => {
            openWizard(true);
          }}
        >
          <PencilAltIcon />
        </Button>
      </Td>
    </Tr>
  );
  return (
    <>
      <Toolbar>
        <ToolbarContent>
          <ToolbarItem>
            <Button
              onClick={() => {
                openWizard(true);
              }}
              variant="secondary"
            >
              {isShowingRules ? t`Add RRules` : t`Add Exception`}
            </Button>
          </ToolbarItem>
          <ToolbarItem>
            <Switch
              label={t`Occurances`}
              labelOff={t`Exceptions`}
              isChecked={isShowingRules}
              onChange={(isChecked) => {
                setIsShowingRules(isChecked);
              }}
            />
          </ToolbarItem>
        </ToolbarContent>
      </Toolbar>
      <div css="overflow: auto">
        {frequencies.value[0].frequency === '' &&
        frequencies.value.length < 2 ? (
          <ContentEmpty title={t`RRules`} message={t`Add RRules`} />
        ) : (
          <TableComposable aria-label={t`RRules`} ouiaId="rrules-list">
            <Thead>
              <Tr>
                <Th>{t`Frequency`}</Th>
                <Th>{t`RRule`}</Th>
                <Th>{t`Ending`}</Th>
                <Th>{t`Actions`}</Th>
              </Tr>
            </Thead>
            <Tbody>{frequencies.value.map((freq, i) => list(freq, i))}</Tbody>
          </TableComposable>
        )}
      </div>
    </>
  );
}

export default FrequenciesList;
