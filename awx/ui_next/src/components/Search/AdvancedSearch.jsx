import 'styled-components/macro';
import React, { useState } from 'react';
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
import { useConfig } from '../../contexts/Config';
import getDocsBaseUrl from '../../util/getDocsBaseUrl';

const AdvancedGroup = styled.div`
  display: flex;

  @media (max-width: 991px) {
    display: grid;
    grid-gap: var(--pf-c-toolbar__expandable-content--m-expanded--GridRowGap);
  }
`;

function AdvancedSearch({
  onSearch,
  searchableKeys,
  relatedSearchableKeys,
  maxSelectHeight,
}) {
  // TODO: blocked by pf bug, eventually separate these into two groups in the select
  // for now, I'm spreading set to get rid of duplicate keys...when they are grouped
  // we might want to revisit that.
  const allKeys = [
    ...new Set([...(searchableKeys || []), ...(relatedSearchableKeys || [])]),
  ];

  const [isPrefixDropdownOpen, setIsPrefixDropdownOpen] = useState(false);
  const [isLookupDropdownOpen, setIsLookupDropdownOpen] = useState(false);
  const [isKeyDropdownOpen, setIsKeyDropdownOpen] = useState(false);
  const [prefixSelection, setPrefixSelection] = useState(null);
  const [lookupSelection, setLookupSelection] = useState(null);
  const [keySelection, setKeySelection] = useState(null);
  const [searchValue, setSearchValue] = useState('');
  const config = useConfig();

  const handleAdvancedSearch = e => {
    // keeps page from fully reloading
    e.preventDefault();

    if (searchValue) {
      const actualPrefix = prefixSelection === 'and' ? null : prefixSelection;
      let actualSearchKey;
      // TODO: once we are able to group options for the key typeahead, we will
      // probably want to be able to which group a key was clicked in for duplicates,
      // rather than checking to make sure it's not in both for this appending
      // __search logic
      if (
        relatedSearchableKeys.indexOf(keySelection) > -1 &&
        searchableKeys.indexOf(keySelection) === -1 &&
        keySelection.indexOf('__') === -1
      ) {
        actualSearchKey = `${keySelection}__search`;
      } else {
        actualSearchKey = [actualPrefix, keySelection, lookupSelection]
          .filter(val => !!val)
          .join('__');
      }
      onSearch(actualSearchKey, searchValue);
      setSearchValue('');
    }
  };

  const handleAdvancedTextKeyDown = e => {
    if (e.key && e.key === 'Enter') {
      handleAdvancedSearch(e);
    }
  };

  return (
    <AdvancedGroup>
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
        <SelectOption
          id="not-option-select"
          key="not"
          value="not"
          description={t`Returns results that have values other than this one as well as other filters.`}
        />
      </Select>
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
        {allKeys.map(optionKey => (
          <SelectOption
            key={optionKey}
            value={optionKey}
            id={`select-option-${optionKey}`}
          >
            {optionKey}
          </SelectOption>
        ))}
      </Select>
      <Select
        ouiaId="set-lookup-typeahead"
        aria-label={t`Lookup select`}
        className="lookupSelect"
        variant={SelectVariant.typeahead}
        typeAheadAriaLabel={t`Lookup typeahead`}
        onToggle={setIsLookupDropdownOpen}
        onSelect={(event, selection) => setLookupSelection(selection)}
        onClear={() => setLookupSelection(null)}
        selections={lookupSelection}
        isOpen={isLookupDropdownOpen}
        placeholderText={t`Lookup type`}
        maxHeight={maxSelectHeight}
        noResultsFoundText={t`No results found`}
      >
        <SelectOption
          id="exact-option-select"
          key="exact"
          value="exact"
          description={t`Exact match (default lookup if not specified).`}
        />
        <SelectOption
          id="iexact-option-select"
          key="iexact"
          value="iexact"
          description={t`Case-insensitive version of exact.`}
        />
        <SelectOption
          id="contains-option-select"
          key="contains"
          value="contains"
          description={t`Field contains value.`}
        />
        <SelectOption
          id="icontains-option-select"
          key="icontains"
          value="icontains"
          description={t`Case-insensitive version of contains`}
        />
        <SelectOption
          id="startswith-option-select"
          key="startswith"
          value="startswith"
          description={t`Field starts with value.`}
        />
        <SelectOption
          id="istartswith-option-select"
          key="istartswith"
          value="istartswith"
          description={t`Case-insensitive version of startswith.`}
        />
        <SelectOption
          id="endswith-option-select"
          key="endswith"
          value="endswith"
          description={t`Field ends with value.`}
        />
        <SelectOption
          id="iendswith-option-select"
          key="iendswith"
          value="iendswith"
          description={t`Case-insensitive version of endswith.`}
        />
        <SelectOption
          id="regex-option-select"
          key="regex"
          value="regex"
          description={t`Field matches the given regular expression.`}
        />
        <SelectOption
          id="iregex-option-select"
          key="iregex"
          value="iregex"
          description={t`Case-insensitive version of regex.`}
        />
        <SelectOption
          id="gt-option-select"
          key="gt"
          value="gt"
          description={t`Greater than comparison.`}
        />
        <SelectOption
          id="gte-option-select"
          key="gte"
          value="gte"
          description={t`Greater than or equal to comparison.`}
        />
        <SelectOption
          id="lt-option-select"
          key="lt"
          value="lt"
          description={t`Less than comparison.`}
        />
        <SelectOption
          id="lte-option-select"
          key="lte"
          value="lte"
          description={t`Less than or equal to comparison.`}
        />
        <SelectOption
          id="isnull-option-select"
          key="isnull"
          value="isnull"
          description={t`Check whether the given field or related object is null; expects a boolean value.`}
        />
        <SelectOption
          id="in-option-select"
          key="in"
          value="in"
          description={t`Check whether the given field's value is present in the list provided; expects a comma-separated list of items.`}
        />
      </Select>
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
};

AdvancedSearch.defaultProps = {
  searchableKeys: [],
  relatedSearchableKeys: [],
  maxSelectHeight: '300px',
};

export default AdvancedSearch;
