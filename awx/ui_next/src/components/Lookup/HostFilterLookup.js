import React, { useState, useEffect, useCallback } from 'react';
import { useHistory, useLocation } from 'react-router-dom';
import { number, func, bool, string } from 'prop-types';

import styled from 'styled-components';
import { t } from '@lingui/macro';
import { SearchIcon } from '@patternfly/react-icons';
import {
  Button,
  ButtonVariant,
  Chip,
  FormGroup,
  InputGroup,
  Modal,
  Tooltip,
} from '@patternfly/react-core';
import { HostsAPI } from 'api';
import { getQSConfig, mergeParams, parseQueryString } from 'util/qs';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import ChipGroup from '../ChipGroup';
import Popover from '../Popover';
import DataListToolbar from '../DataListToolbar';
import LookupErrorMessage from './shared/LookupErrorMessage';
import PaginatedTable, { HeaderCell, HeaderRow } from '../PaginatedTable';
import HostListItem from './HostListItem';
import {
  removeDefaultParams,
  removeNamespacedKeys,
  toHostFilter,
  toQueryString,
  toSearchParams,
} from './shared/HostFilterUtils';

const ChipHolder = styled.div`
  && {
    --pf-c-form-control--Height: auto;
  }
  .pf-c-chip-group {
    margin-right: 8px;
  }
`;

const ModalList = styled.div`
  .pf-c-toolbar__content {
    padding: 0 !important;
  }
`;

const useModal = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  function toggleModal() {
    setIsModalOpen(!isModalOpen);
  }

  function closeModal() {
    setIsModalOpen(false);
  }

  return {
    isModalOpen,
    toggleModal,
    closeModal,
  };
};

const QS_CONFIG = getQSConfig(
  'smart_hosts',
  {
    page: 1,
    page_size: 5,
    order_by: 'name',
  },
  ['id', 'page', 'page_size', 'inventory']
);

const buildSearchColumns = () => [
  {
    name: t`Name`,
    key: 'name__icontains',
    isDefault: true,
  },
  {
    name: t`ID`,
    key: 'id',
  },
  {
    name: t`Group`,
    key: 'groups__name__icontains',
  },
  {
    name: t`Inventory ID`,
    key: 'inventory',
  },
  {
    name: t`Enabled`,
    key: 'enabled',
    isBoolean: true,
  },
  {
    name: t`Instance ID`,
    key: 'instance_id',
  },
  {
    name: t`Last job`,
    key: 'last_job',
  },
  {
    name: t`Insights system ID`,
    key: 'insights_system_id',
  },
];

function HostFilterLookup({
  helperTextInvalid,
  isValid,
  isDisabled,
  onBlur,
  onChange,
  organizationId,
  value,
  enableNegativeFiltering,
  enableRelatedFuzzyFiltering,
}) {
  const history = useHistory();
  const location = useLocation();
  const [chips, setChips] = useState({});
  const [queryString, setQueryString] = useState('');
  const { isModalOpen, toggleModal, closeModal } = useModal();
  const searchColumns = buildSearchColumns();

  const parseRelatedSearchFields = (searchFields) => {
    if (searchFields.indexOf('__search') !== -1) {
      return searchFields.slice(0, -8);
    }
    return searchFields;
  };

  const {
    result: { count, hosts, relatedSearchableKeys, searchableKeys },
    error: contentError,
    request: fetchHosts,
    isLoading,
  } = useRequest(
    useCallback(
      async (orgId) => {
        const params = parseQueryString(QS_CONFIG, location.search);
        const [{ data }, { data: actions }] = await Promise.all([
          HostsAPI.read(
            mergeParams(params, { inventory__organization: orgId })
          ),
          HostsAPI.readOptions(),
        ]);
        return {
          count: data.count,
          hosts: data.results,
          relatedSearchableKeys: (actions?.related_search_fields || []).map(
            parseRelatedSearchFields
          ),
          searchableKeys: Object.keys(actions?.actions.GET || {}).filter(
            (key) => actions.actions?.GET[key].filterable
          ),
        };
      },
      [location.search]
    ),
    {
      count: 0,
      hosts: [],
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  const { error, dismissError } = useDismissableError(contentError);

  useEffect(() => {
    if (isModalOpen && organizationId) {
      dismissError();
      fetchHosts(organizationId);
    }
  }, [fetchHosts, organizationId, isModalOpen]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const filters = toSearchParams(value);
    setQueryString(toQueryString(QS_CONFIG, filters));
    setChips(buildChips(filters));
  }, [value]);

  function qsToHostFilter(qs) {
    const searchParams = toSearchParams(qs);
    const withoutNamespace = removeNamespacedKeys(QS_CONFIG, searchParams);
    const withoutDefaultParams = removeDefaultParams(
      QS_CONFIG,
      withoutNamespace
    );
    return toHostFilter(withoutDefaultParams);
  }

  const save = () => {
    const hostFilterString = qsToHostFilter(location.search);
    onChange(hostFilterString);
    closeModal();
    history.replace({
      pathname: `${location.pathname}`,
      search: '',
    });
  };

  function buildChips(filter = {}) {
    const inputGroupChips = Object.keys(filter).reduce((obj, param) => {
      const parsedKey = param.replace('or__', '');
      const chipsArray = [];

      if (Array.isArray(filter[param])) {
        filter[param].forEach((val) =>
          chipsArray.push({
            key: `${param}:${val}`,
            node: `${val}`,
          })
        );
      } else {
        chipsArray.push({
          key: `${param}:${filter[param]}`,
          node: `${filter[param]}`,
        });
      }

      obj[parsedKey] = {
        key: parsedKey,
        label: filter[param],
        chips: [...chipsArray],
      };

      return obj;
    }, {});

    return inputGroupChips;
  }

  const handleOpenModal = () => {
    history.replace({
      pathname: `${location.pathname}`,
      search: queryString,
    });
    toggleModal();
  };

  const handleClose = () => {
    closeModal();
    history.replace({
      pathname: `${location.pathname}`,
      search: '',
    });
  };

  const renderLookup = () => (
    <InputGroup onBlur={onBlur}>
      <Button
        ouiaId="host-filter-search-button"
        aria-label={t`Search`}
        id="host-filter"
        isDisabled={isDisabled}
        onClick={handleOpenModal}
        variant={ButtonVariant.control}
      >
        <SearchIcon />
      </Button>
      <ChipHolder className="pf-c-form-control">
        {searchColumns.map(({ name, key }) => (
          <ChipGroup
            categoryName={name}
            key={name}
            numChips={5}
            totalChips={chips[key]?.chips?.length || 0}
          >
            {chips[key]?.chips?.map((chip) => (
              <Chip key={chip.key} isReadOnly>
                {chip.node}
              </Chip>
            ))}
          </ChipGroup>
        ))}
        {/* Parse advanced search chips */}
        {Object.keys(chips).length > 0 &&
          Object.keys(chips)
            .filter((val) => chips[val].chips.length > 0)
            .filter(
              (val) => searchColumns.map((val2) => val2.key).indexOf(val) === -1
            )
            .map((leftoverKey) => (
              <ChipGroup
                categoryName={chips[leftoverKey].key}
                key={chips[leftoverKey].key}
                numChips={5}
                totalChips={chips[leftoverKey]?.chips?.length || 0}
              >
                {chips[leftoverKey]?.chips?.map((chip) => (
                  <Chip key={chip.key} isReadOnly>
                    {chip.node}
                  </Chip>
                ))}
              </ChipGroup>
            ))}
      </ChipHolder>
    </InputGroup>
  );

  return (
    <FormGroup
      fieldId="host-filter"
      helperTextInvalid={helperTextInvalid}
      isRequired
      label={t`Smart host filter`}
      validated={isValid ? 'default' : 'error'}
      labelIcon={
        <Popover
          content={t`Populate the hosts for this inventory by using a search
              filter. Example: ansible_facts.ansible_distribution:"RedHat".
              Refer to the documentation for further syntax and
              examples.  Refer to the Ansible Tower documentation for further syntax and
              examples.`}
        />
      }
    >
      {isDisabled ? (
        <Tooltip
          content={t`Please select an organization before editing the host filter`}
        >
          {renderLookup()}
        </Tooltip>
      ) : (
        renderLookup()
      )}
      <Modal
        aria-label={t`Lookup modal`}
        isOpen={isModalOpen}
        onClose={handleClose}
        title={t`Perform a search to define a host filter`}
        variant="large"
        actions={[
          <Button
            ouiaId="host-filter-modal-select-button"
            isDisabled={!location.search}
            key="select"
            onClick={save}
            variant="primary"
          >
            {t`Select`}
          </Button>,
          <Button
            ouiaId="host-filter-modal-cancel-button"
            key="cancel"
            variant="link"
            onClick={handleClose}
          >
            {t`Cancel`}
          </Button>,
        ]}
      >
        <ModalList>
          <PaginatedTable
            contentError={error}
            hasContentLoading={isLoading}
            itemCount={count}
            items={hosts}
            pluralizedItemName={t`hosts`}
            qsConfig={QS_CONFIG}
            headerRow={
              <HeaderRow qsConfig={QS_CONFIG} isSelectable={false}>
                <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
                <HeaderCell>{t`Inventory`}</HeaderCell>
              </HeaderRow>
            }
            renderRow={(item) => <HostListItem key={item.id} item={item} />}
            renderToolbar={(props) => (
              <DataListToolbar
                {...props}
                fillWidth
                enableNegativeFiltering={enableNegativeFiltering}
                enableRelatedFuzzyFiltering={enableRelatedFuzzyFiltering}
              />
            )}
            toolbarSearchColumns={searchColumns}
            toolbarSearchableKeys={searchableKeys}
            toolbarRelatedSearchableKeys={relatedSearchableKeys}
          />
        </ModalList>
      </Modal>
      <LookupErrorMessage error={error} />
    </FormGroup>
  );
}

HostFilterLookup.propTypes = {
  isValid: bool,
  onBlur: func,
  onChange: func,
  organizationId: number,
  value: string,
  enableNegativeFiltering: bool,
  enableRelatedFuzzyFiltering: bool,
};
HostFilterLookup.defaultProps = {
  isValid: true,
  onBlur: () => {},
  onChange: () => {},
  organizationId: null,
  value: '',
  enableNegativeFiltering: true,
  enableRelatedFuzzyFiltering: true,
};

export default HostFilterLookup;
