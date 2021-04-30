import React from 'react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import {
  DataListItem,
  DataListItemRow,
  DataListItemCells,
} from '@patternfly/react-core';

import DataListCell from '../../../components/DataListCell';

function ExecutionEnvironmentTemplateListItem({ template, detailUrl }) {
  return (
    <DataListItem
      key={template.id}
      aria-labelledby={`check-action-${template.id}`}
      id={`${template.id}`}
    >
      <DataListItemRow>
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name" aria-label={t`Name`}>
              <Link to={`${detailUrl}`}>
                <b>{template.name}</b>
              </Link>
            </DataListCell>,
            <DataListCell key="template-type" aria-label={t`Template type`}>
              {template.type === 'job_template'
                ? t`Job Template`
                : t`Workflow Job Template`}
            </DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}

export default ExecutionEnvironmentTemplateListItem;
