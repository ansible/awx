import React from 'react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import { Tr, Td } from '@patternfly/react-table';

function ExecutionEnvironmentTemplateListItem({ template, detailUrl }) {
  return (
    <Tr
      id={`template-row-${template.id}`}
      ouiaId={`template-row-${template.id}`}
    >
      <Td dataLabel={t`Name`}>
        <Link to={`${detailUrl}`}>
          <b>{template.name}</b>
        </Link>
      </Td>
      <Td dataLabel={t`Type`}>
        {template.type === 'job_template'
          ? t`Job Template`
          : t`Workflow Job Template`}
      </Td>
    </Tr>
  );
}

export default ExecutionEnvironmentTemplateListItem;
