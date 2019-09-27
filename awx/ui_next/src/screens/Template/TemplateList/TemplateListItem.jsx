import React, { Component } from 'react';
import { Link } from 'react-router-dom';
import {
  DataListItem,
  DataListItemRow,
  DataListItemCells,
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
              <DataListCell key="divider">
                <VerticalSeparator />
                <span>
                  <Link to={`/templates/${template.type}/${template.id}`}>
                    <b>{template.name}</b>
                  </Link>
                </span>
              </DataListCell>,
              <DataListCell key="type">
                {toTitleCase(template.type)}
              </DataListCell>,
              <DataListCell key="sparkline">
                <Sparkline jobs={template.summary_fields.recent_jobs} />
              </DataListCell>,
              <DataListCell lastcolumn="true" key="launch">
                {canLaunch && template.type === 'job_template' && (
                  <Tooltip content={i18n._(t`Launch`)} position="top">
                    <LaunchButton resource={template}>
                      {({ handleLaunch }) => (
                        <StyledButton variant="plain" onClick={handleLaunch}>
                          <RocketIcon />
                        </StyledButton>
                      )}
                    </LaunchButton>
                  </Tooltip>
                )}
              </DataListCell>,
            ]}
          />
        </DataListItemRow>
      </DataListItem>
    );
  }
}
export { TemplateListItem as _TemplateListItem };
export default withI18n()(TemplateListItem);
