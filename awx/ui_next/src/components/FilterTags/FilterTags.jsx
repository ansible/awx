import React, { Fragment } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { DataToolbarGroup, DataToolbarItem } from '@patternfly/react-core/dist/esm/experimental';
import { parseQueryString } from '@util/qs';
import { Button, Chip, ChipGroup, ChipGroupToolbarItem } from '@patternfly/react-core';
import VerticalSeparator from '@components/VerticalSeparator';

const ResultCount = styled.span`
  font-weight: bold;
`;

const FilterLabel = styled.span`
  padding-right: 20px;
`;

// remove non-default query params so they don't show up as filter tags
const filterDefaultParams = (paramsArr, config) => {
  const defaultParamsKeys = Object.keys(config.defaultParams);
  return paramsArr.filter(key => defaultParamsKeys.indexOf(key) === -1);
};

const FilterTags = ({
  i18n,
  itemCount,
  qsConfig,
  location,
  onRemove,
  onRemoveAll,
}) => {
  const queryParams = parseQueryString(qsConfig, location.search);
  const queryParamsByKey = {};
  const nonDefaultParams = filterDefaultParams(
    Object.keys(queryParams),
    qsConfig
  );
  nonDefaultParams.forEach(key => {
    const label = key
      .replace('__icontains', '')
      .split('_')
      .map(word => `${word.charAt(0).toUpperCase()}${word.slice(1)}`)
      .join(' ');
      queryParamsByKey[key] = { label, tags: [] };

    if (Array.isArray(queryParams[key])) {
      queryParams[key].forEach(val =>
        queryParamsByKey[key].tags.push(val)
      );
    } else {
      queryParamsByKey[key].tags.push(queryParams[key]);
    }
  });

  return (
    Object.keys(queryParamsByKey).length > 0 && (
      <Fragment>
        <DataToolbarGroup>
          <ResultCount>{i18n._(t`${itemCount} results`)}</ResultCount>
        </DataToolbarGroup>
        <DataToolbarGroup>
          <FilterLabel>{i18n._(t`Active Filters:`)}</FilterLabel>
          <DataToolbarItem variant="chip-group">
            {Object.keys(queryParamsByKey).map(key => (
              <ChipGroup withToolbar key={`${key}-group`}>
                <ChipGroupToolbarItem key={key} categoryName={queryParamsByKey[key].label}>
                  {queryParamsByKey[key].tags.map(chip => (
                      <Chip key={chip} onClick={() => onRemove(key, chip)}>
                        {chip}
                      </Chip>
                  ))}
                </ChipGroupToolbarItem>
              </ChipGroup>
            ))}
          </DataToolbarItem>
          <DataToolbarItem>
            <Button variant="link" onClick={onRemoveAll} isInline>
              {i18n._(t`Clear all search filters`)}
            </Button>
          </DataToolbarItem>
        </DataToolbarGroup>
      </Fragment>
    )
  );
};

export default withI18n()(withRouter(FilterTags));
