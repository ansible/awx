import React from 'react';
import styled, { css } from 'styled-components';
import {
  Pagination as PFPagination,
  DropdownDirection,
} from '@patternfly/react-core';
import { t } from '@lingui/macro';

const AWXPagination = styled(PFPagination)`
  ${(props) =>
    props.perPageOptions &&
    !props.perPageOptions.length &&
    css`
      .pf-c-options-menu__toggle-button {
        display: none;
      }
    `}
`;

export default (props) => (
  <AWXPagination
    ouiaId="pagination"
    titles={{
      items: t`items`,
      page: t`page`,
      pages: t`pages`,
      itemsPerPage: t`Items per page`,
      perPageSuffix: t`per page`,
      toFirstPage: t`Go to first page`,
      toPreviousPage: t`Go to previous page`,
      toLastPage: t`Go to last page`,
      toNextPage: t`Go to next page`,
      optionsToggle: t`Select`,
      currPage: t`Current page`,
      paginationTitle: t`Pagination`,
      ofWord: t`of`,
    }}
    dropDirection={DropdownDirection.up}
    {...props}
  />
);
