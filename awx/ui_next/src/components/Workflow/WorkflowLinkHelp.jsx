import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';

const GridDL = styled.dl`
  display: grid;
  grid-template-columns: max-content;
  column-gap: 15px;
  row-gap: 0px;
  dt {
    grid-column-start: 1;
  }
  dd {
    grid-column-start: 2;
  }
`;

function WorkflowLinkHelp({ link, i18n }) {
  let linkType;
  switch (link.edgeType) {
    case 'always':
      linkType = i18n._(t`Always`);
      break;
    case 'success':
      linkType = i18n._(t`On Success`);
      break;
    case 'failure':
      linkType = i18n._(t`On Failure`);
      break;
    default:
      linkType = '';
  }

  return (
    <GridDL>
      <dt>
        <b>{i18n._(t`Run`)}</b>
      </dt>
      <dd>{linkType}</dd>
    </GridDL>
  );
}

export default withI18n()(WorkflowLinkHelp);
