import React from 'react';
import { Link } from 'react-router-dom';
import {
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  TextContent,
} from '@patternfly/react-core';
import styled from 'styled-components';
import DataListCell from '../DataListCell';

const DetailWrapper = styled(TextContent)`
  display: grid;
  grid-template-columns:
    minmax(70px, max-content)
    repeat(auto-fit, minmax(60px, max-content));
  grid-gap: 10px;
`;

export default function PaginatedDataListItem({ item }) {
  return (
    <DataListItem
      aria-labelledby={`items-list-item-${item.id}`}
      key={item.id}
      id={`${item.id}`}
    >
      <DataListItemRow>
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name">
              <DetailWrapper>
                <Link to={{ pathname: item.url }}>
                  <b id={`items-list-item-${item.id}`}>{item.name}</b>
                </Link>
              </DetailWrapper>
            </DataListCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}
