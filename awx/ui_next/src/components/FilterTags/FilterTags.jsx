import React from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { Button } from '@patternfly/react-core';
import { parseQueryString } from '@util/qs';
import { ChipGroup, Chip } from '@components/Chip';
import VerticalSeparator from '@components/VerticalSeparator';

const FilterTagsRow = styled.div`
    display: flex;
    padding: 15px 20px;
    border-top: 1px solid #d2d2d2;
    font-size: 14px;
    align-items: center;
`;

const ResultCount = styled.span`
    font-weight: bold;
`;

const FilterLabel = styled.span`
    padding-right: 20px;
`;

// remove non-default query params so they don't show up as filter tags
const filterOutDefaultParams = (paramsArr, config) => {
  const defaultParamsKeys = Object.keys(config.defaultParams);
  return paramsArr.filter(key => defaultParamsKeys.indexOf(key) === -1);
};

const FilterTags = ({ i18n, itemCount, qsConfig, location, onRemove, onRemoveAll }) => {
  const queryParams = parseQueryString(qsConfig, location.search);
  const queryParamsArr = [];
  const displayAll = true;
  const nonDefaultParams = filterOutDefaultParams(Object.keys(queryParams), qsConfig);
  nonDefaultParams
    .forEach(key => {
      if (Array.isArray(queryParams[key])) {
        queryParams[key].forEach(val => queryParamsArr.push({ key, value: val }));
      } else {
        queryParamsArr.push({ key, value: queryParams[key] });
      }
    });

  return (queryParamsArr.length > 0) && (
    <FilterTagsRow>
      <ResultCount>
        {`${itemCount} results`}
      </ResultCount>
      <VerticalSeparator />
      <FilterLabel>Active Filters:</FilterLabel>
      <ChipGroup displayAll={displayAll}>
        {queryParamsArr.map(param => (
          <Chip
            className="searchTagChip"
            key={`${param.key}__${param.value}`}
            isReadOnly={false}
            onClick={() => onRemove(param)}
          >
            {param.value}
          </Chip>
        ))}
        <div className="pf-c-chip pf-m-overflow">
          <Button
            variant="plain"
            type="button"
            aria-label={i18n._(t`Clear all search filters`)}
            onClick={onRemoveAll}
          >
            <span className="pf-c-chip__text">{i18n._(t`Clear all`)}</span>
          </Button>
        </div>
      </ChipGroup>
    </FilterTagsRow>
  );
};

export default withI18n()(withRouter(FilterTags));
