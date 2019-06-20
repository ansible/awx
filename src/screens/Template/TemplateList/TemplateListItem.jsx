import React, { Component } from 'react';
import { Link } from 'react-router-dom';
import {
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  DataListCheck,
  DataListCell as PFDataListCell,
} from '@patternfly/react-core';
import styled from 'styled-components';

import VerticalSeparator from '@components/VerticalSeparator';
import LaunchButton from '@components/LaunchButton';
import { toTitleCase } from '@util/strings';

const DataListCell = styled(PFDataListCell)`
  display: flex;
  align-items: center;
  @media screen and (min-width: 768px) {
    padding-bottom: 0;
    justify-content: ${props => (props.lastcolumn ? 'flex-end' : 'inherit')};
  }
`;

class TemplateListItem extends Component {
  render () {
    const {
      template,
      isSelected,
      onSelect,
    } = this.props;
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
          <DataListItemCells dataListCells={[
            <DataListCell key="divider">
              <VerticalSeparator />
              <span>
                <Link to={`/templates/${template.type}/${template.id}`}>
                  <b>{template.name}</b>
                </Link>
              </span>
            </DataListCell>,
            <DataListCell key="type">{toTitleCase(template.type)}</DataListCell>,
            <DataListCell lastcolumn="true" key="launch">
              {canLaunch && template.type === 'job_template' && (
                <LaunchButton
                  templateId={template.id}
                />
              )}
            </DataListCell>
          ]}
          />
        </DataListItemRow>
      </DataListItem>
    );
  }
}
export { TemplateListItem as _TemplateListItem };
export default TemplateListItem;
