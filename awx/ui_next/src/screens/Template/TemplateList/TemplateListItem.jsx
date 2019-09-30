import React, { Component } from 'react';
import { Link } from 'react-router-dom';
import {
  DataListItem,
  DataListItemRow,
  DataListItemCells as PFDataListItemCells,
  Tooltip,
  Button as PFButton,
} from '@patternfly/react-core';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { RocketIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

import DataListCell from '@components/DataListCell';
import DataListCheck from '@components/DataListCheck';
import LaunchButton from '@components/LaunchButton';
import VerticalSeparator from '@components/VerticalSeparator';
import { Sparkline } from '@components/Sparkline';
import { toTitleCase } from '@util/strings';

const StyledButton = styled(PFButton)`
  padding: 5px 8px;
  border: none;
  &:hover {
    background-color: #0066cc;
    color: white;
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
  @media screen and (max-width: 768px) {
    && {
      padding-top: 0px;
      flex: 0 0 33%;
      padding-right: 20px;
    }
  }
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
              <RightDataListCell
                css="max-width: 40px;"
                righthalf="true"
                lastcolumn="true"
                key="launch"
              >
                {canLaunch && template.type === 'job_template' && (
                  <Tooltip content={i18n._(t`Launch`)} position="top">
                    <LaunchButton
                      component={Link}
                      to="/templates"
                      templateId={template.id}
                    >
                      {handleLaunch => (
                        <StyledButton variant="plain" onClick={handleLaunch}>
                          <RocketIcon />
                        </StyledButton>
                      )}
                    </LaunchButton>
                  </Tooltip>
                )}
              </RightDataListCell>,
            ]}
          />
        </DataListItemRow>
      </DataListItem>
    );
  }
}
export { TemplateListItem as _TemplateListItem };
export default withI18n()(TemplateListItem);
