import 'styled-components/macro';
import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { t } from '@lingui/macro';
import {
  Button,
  ButtonVariant,
  InputGroup,
  Select,
  SelectOption,
  SelectVariant,
  TextInput,
  Tooltip,
} from '@patternfly/react-core';
import { SearchIcon, QuestionCircleIcon } from '@patternfly/react-icons';
import styled from 'styled-components';
import { useConfig } from 'contexts/Config';
import getDocsBaseUrl from 'util/getDocsBaseUrl';
import RelatedLookupTypeInput from './RelatedLookupTypeInput';
import LookupTypeInput from './LookupTypeInput';

const AdvancedGroup = styled.div`
  display: flex;

  @media (max-width: 991px) {
    display: grid;
    grid-gap: var(--pf-c-toolbar__expandable-content--m-expanded--GridRowGap);
  }

  & .pf-c-select {
    min-width: 150px;
  }
`;

function AdvancedSearch({
  onSearch,
  searchableKeys,
  relatedSearchableKeys,
  maxSelectHeight,
  enableNegativeFiltering,
  enableRelatedFuzzyFiltering,
}) {
  // TODO: blocked by pf bug, eventually separate these into two groups in the select
  // for now, I'm spreading set to get rid of duplicate keys...when they are grouped
  // we might want to revisit that.
  const allKeys = [
    ...new Set([
      ...(searchableKeys.map((k) => k.key) || []),
      ...(relatedSearchableKeys || []),
    ]),
  ];

  const [isPrefixDropdownOpen, setIsPrefixDropdownOpen] = useState(false);
  const [isKeyDropdownOpen, setIsKeyDropdownOpen] = useState(false);
  const [prefixSelection, setPrefixSelection] = useState(null);
  const [lookupSelection, setLookupSelection] = useState(null);
  const [keySelection, setKeySelection] = useState(null);
  const [searchValue, setSearchValue] = useState('');
  // const [relatedSearchKeySelected, setRelatedSearchKeySelected] =
  //   useState(false);
  const config = useConfig();

  const relatedSearchKeySelected =
    keySelection &&
    relatedSearchableKeys.indexOf(keySelection) > -1 &&
    !searchableKeys.find((k) => k.key === keySelection);
  const lookupKeyType =
    keySelection && !relatedSearchKeySelected
      ? searchableKeys.find((k) => k.key === keySelection).type
      : null;

  useEffect(() => {
    if (relatedSearchKeySelected) {
      setLookupSelection('name__icontains');
    } else {
      setLookupSelection(null);
    }
  }, [keySelection]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (lookupSelection === 'search') {
      setPrefixSelection(null);
    }
  }, [lookupSelection]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleAdvancedSearch = (e) => {
    // keeps page from fully reloading
    e.preventDefault();

    if (searchValue) {
      const actualPrefix = prefixSelection === 'and' ? null : prefixSelection;
      const actualSearchKey = [actualPrefix, keySelection, lookupSelection]
        .filter((val) => !!val)
        .join('__');
      onSearch(actualSearchKey, searchValue);
      setSearchValue('');
    }
  };

  const handleAdvancedTextKeyDown = (e) => {
    if (e.key && e.key === 'Enter') {
      handleAdvancedSearch(e);
    }
  };

  const renderSetType = () => (
    <Select
      ouiaId="set-type-typeahead"
      aria-label={t`Set type select`}
      className="setTypeSelect"
      variant={SelectVariant.typeahead}
      typeAheadAriaLabel={t`Set type typeahead`}
      onToggle={setIsPrefixDropdownOpen}
      onSelect={(event, selection) => setPrefixSelection(selection)}
      onClear={() => setPrefixSelection(null)}
      selections={prefixSelection}
      isOpen={isPrefixDropdownOpen}
      placeholderText={t`Set type`}
      maxHeight={maxSelectHeight}
      noResultsFoundText={t`No results found`}
      isDisabled={lookupSelection === 'search'}
    >
      <SelectOption
        id="and-option-select"
        key="and"
        value="and"
        description={t`Returns results that satisfy this one as well as other filters.  This is the default set type if nothing is selected.`}
      />
      <SelectOption
        id="or-option-select"
        key="or"
        value="or"
        description={t`Returns results that satisfy this one or any other filters.`}
      />
      {enableNegativeFiltering && (
        <SelectOption
          id="not-option-select"
          key="not"
          value="not"
          description={t`Returns results that have values other than this one as well as other filters.`}
        />
      )}
    </Select>
  );

  return (
    <AdvancedGroup>
      {lookupSelection === 'search' ? (
        <Tooltip
          content={t`Set type disabled for related search field fuzzy searches`}
        >
          {renderSetType()}
        </Tooltip>
      ) : (
        renderSetType()
      )}
      <Select
        ouiaId="set-key-typeahead"
        aria-label={t`Key select`}
        className="keySelect"
        variant={SelectVariant.typeahead}
        typeAheadAriaLabel={t`Key typeahead`}
        onToggle={setIsKeyDropdownOpen}
        onSelect={(event, selection) => setKeySelection(selection)}
        onClear={() => setKeySelection(null)}
        selections={keySelection}
        isOpen={isKeyDropdownOpen}
        placeholderText={t`Key`}
        isCreatable
        onCreateOption={setKeySelection}
        maxHeight={maxSelectHeight}
        noResultsFoundText={t`No results found`}
      >
        {allKeys.map((optionKey) => (
          <SelectOption
            key={optionKey}
            value={optionKey}
            id={`select-option-${optionKey}`}
          >
            {optionKey}
          </SelectOption>
        ))}
      </Select>
      {relatedSearchKeySelected ? (
        <RelatedLookupTypeInput
          value={lookupSelection}
          setValue={setLookupSelection}
          maxSelectHeight={maxSelectHeight}
          enableFuzzyFiltering={enableRelatedFuzzyFiltering}
        />
      ) : (
        <LookupTypeInput
          value={lookupSelection}
          type={lookupKeyType}
          setValue={setLookupSelection}
          maxSelectHeight={maxSelectHeight}
        />
      )}
      <InputGroup>
        <TextInput
          data-cy="advanced-search-text-input"
          type="search"
          aria-label={t`Advanced search value input`}
          isDisabled={!keySelection}
          value={(!keySelection && t`First, select a key`) || searchValue}
          onChange={setSearchValue}
          onKeyDown={handleAdvancedTextKeyDown}
        />
        <div css={!searchValue && `cursor:not-allowed`}>
          <Button
            ouiaId="advanced-search-text-input"
            variant={ButtonVariant.control}
            isDisabled={!searchValue}
            aria-label={t`Search submit button`}
            onClick={handleAdvancedSearch}
          >
            <SearchIcon />
          </Button>
        </div>
      </InputGroup>
      <Tooltip content={t`Advanced search documentation`} position="bottom">
        <Button
          ouiaId="search-docs-button"
          component="a"
          variant="plain"
          target="_blank"
          href={`${getDocsBaseUrl(config)}/html/userguide/search_sort.html`}
        >
          <QuestionCircleIcon />
        </Button>
      </Tooltip>
    </AdvancedGroup>
  );
}

AdvancedSearch.propTypes = {
  onSearch: PropTypes.func.isRequired,
  searchableKeys: PropTypes.arrayOf(PropTypes.string),
  relatedSearchableKeys: PropTypes.arrayOf(PropTypes.string),
  maxSelectHeight: PropTypes.string,
  enableNegativeFiltering: PropTypes.bool,
  enableRelatedFuzzyFiltering: PropTypes.bool,
};

AdvancedSearch.defaultProps = {
  searchableKeys: [],
  relatedSearchableKeys: [],
  maxSelectHeight: '300px',
  enableNegativeFiltering: true,
  enableRelatedFuzzyFiltering: true,
};

export default AdvancedSearch;
