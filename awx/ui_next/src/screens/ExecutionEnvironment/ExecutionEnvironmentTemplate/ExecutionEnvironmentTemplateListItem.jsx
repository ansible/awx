import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import {
  DataListItem,
  DataListItemRow,
  DataListItemCells,
} from '@patternfly/react-core';

import DataListCell from '../../../components/DataListCell';

function ExecutionEnvironmentTemplateListItem({ template, detailUrl, i18n }) {
  return (
    <DataListItem
      key={template.id}
      aria-labelledby={`check-action-${template.id}`}
      id={`${template.id}`}
    >
      <DataListItemRow>
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name" aria-label={i18n._(t`Name`)}>
              <Link to={`${detailUrl}`}>
                <b>{template.name}</b>
              </Link>
            </DataListCell>,
            <DataListCell
              key="template-type"
              aria-label={i18n._(t`Template type`)}
            >
              {template.type === 'job_template'
                ? i18n._(t`Job Template`)
                : i18n._(t`Workflow Job Template`)}
            </DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}

export default withI18n()(ExecutionEnvironmentTemplateListItem);
