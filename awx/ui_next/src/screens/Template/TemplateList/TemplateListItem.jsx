import React, { Component } from 'react';
import { Link } from 'react-router-dom';
import {
  DataListItem,
  DataListItemRow,
  DataListItemCells as PFDataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { PencilAltIcon, RocketIcon } from '@patternfly/react-icons';

import ActionButtonCell from '@components/ActionButtonCell';
import DataListCell from '@components/DataListCell';
import DataListCheck from '@components/DataListCheck';
import LaunchButton from '@components/LaunchButton';
import ListActionButton from '@components/ListActionButton';
import VerticalSeparator from '@components/VerticalSeparator';
import { Sparkline } from '@components/Sparkline';
import { toTitleCase } from '@util/strings';

import styled from 'styled-components';

const rightStyle = `
@media screen and (max-width: 768px) {
  && {
    padding-top: 0px;
    flex: 0 0 33%;
    padding-right: 20px;
  }
}
`;

const DataListItemCells = styled(PFDataListItemCells)`
  display: flex;
  @media screen and (max-width: 768px) {
    flex-wrap: wrap;
    justify-content: space-between;
  }
`;

const LeftDataListCell = styled(DataListCell)`
  @media screen and (max-width: 768px) {
    && {
      padding-bottom: 16px;
      flex: 1 1 100%;
    }
  }
`;
const RightDataListCell = styled(DataListCell)`
  ${rightStyle}
`;
const RightActionButtonCell = styled(ActionButtonCell)`
  ${rightStyle}
`;

class TemplateListItem extends Component {
  render() {
    const { i18n, template, isSelected, onSelect } = this.props;
    const canLaunch = template.summary_fields.user_capabilities.start;

    return (
      <DataListItem
        aria-labelledby={`check-action-${template.id}`}
        css="--pf-c-data-list__expandable-content--BoxShadow: none;"
      >
        <DataListItemRow>
          <DataListCheck
            id={`select-jobTemplate-${template.id}`}
            checked={isSelected}
            onChange={onSelect}
            aria-labelledby={`check-action-${template.id}`}
          />
          <DataListItemCells
            dataListCells={[
              <LeftDataListCell key="divider">
                <VerticalSeparator />
                <span>
                  <Link to={`/templates/${template.type}/${template.id}`}>
                    <b>{template.name}</b>
                  </Link>
                </span>
              </LeftDataListCell>,
              <RightDataListCell
                css="padding-left: 40px;"
                righthalf="true"
                key="type"
              >
                {toTitleCase(template.type)}
              </RightDataListCell>,
              <RightDataListCell
                css="flex: 1;"
                righthalf="true"
                key="sparkline"
              >
                <Sparkline jobs={template.summary_fields.recent_jobs} />
              </RightDataListCell>,
              <RightActionButtonCell
                css="max-width: 80px;"
                righthalf="true"
                lastcolumn="true"
                key="launch"
              >
                {canLaunch && template.type === 'job_template' && (
                  <Tooltip content={i18n._(t`Launch Template`)} position="top">
                    <LaunchButton resource={template}>
                      {({ handleLaunch }) => (
                        <ListActionButton
                          variant="plain"
                          onClick={handleLaunch}
                        >
                          <RocketIcon />
                        </ListActionButton>
                      )}
                    </LaunchButton>
                  </Tooltip>
                )}
                {template.summary_fields.user_capabilities.edit && (
                  <Tooltip content={i18n._(t`Edit Template`)} position="top">
                    <ListActionButton
                      variant="plain"
                      component={Link}
                      to={`/templates/${template.type}/${template.id}/edit`}
                    >
                      <PencilAltIcon />
                    </ListActionButton>
                  </Tooltip>
                )}
              </RightActionButtonCell>,
            ]}
          />
        </DataListItemRow>
      </DataListItem>
    );
  }
}
export { TemplateListItem as _TemplateListItem };
export default withI18n()(TemplateListItem);
