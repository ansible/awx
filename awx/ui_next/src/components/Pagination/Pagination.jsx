import React from 'react';
import styled, { css } from 'styled-components';
import {
  Pagination as PFPagination,
  DropdownDirection,
} from '@patternfly/react-core';
import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';

const AWXPagination = styled(PFPagination)`
  ${props =>
    props.perPageOptions &&
    !props.perPageOptions.length &&
    css`
      .pf-c-options-menu__toggle-button {
        display: none;
      }
    `}
`;

export default props => (
  <I18n>
    {({ i18n }) => (
      <AWXPagination
        titles={{
          items: i18n._(t`items`),
          page: i18n._(t`page`),
          pages: i18n._(t`pages`),
          itemsPerPage: i18n._(t`Items per page`),
          perPageSuffix: i18n._(t`per page`),
          toFirstPage: i18n._(t`Go to first page`),
          toPreviousPage: i18n._(t`Go to previous page`),
          toLastPage: i18n._(t`Go to last page`),
          toNextPage: i18n._(t`Go to next page`),
          optionsToggle: i18n._(t`Select`),
          currPage: i18n._(t`Current page`),
          paginationTitle: i18n._(t`Pagination`),
        }}
        dropDirection={DropdownDirection.up}
        {...props}
      />
    )}
  </I18n>
);
