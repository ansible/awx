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
import { toTitleCase } from '@util/strings';

const DataListCell = styled(PFDataListCell)`
  display: flex;
  align-items: center;
  @media screen and (min-width: 768px) {
    padding-bottom: 0;
  }
`;

class TemplateListItem extends Component {
  render () {
    const {
      template,
      isSelected,
      onSelect,
    } = this.props;

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
                <Link to="/home">
                  <b>{template.name}</b>
                </Link>
              </span>
            </DataListCell>,
            <DataListCell key="type">{toTitleCase(template.type)}</DataListCell>
          ]}
          />
        </DataListItemRow>
      </DataListItem>
    );
  }
}
export { TemplateListItem as _TemplateListItem };
export default TemplateListItem;
