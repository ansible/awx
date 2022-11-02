import 'styled-components/macro';
import React, { useEffect, useState } from 'react';
import { string, func, bool, arrayOf } from 'prop-types';
import { t } from '@lingui/macro';
import {
  Button,
  ButtonVariant,
  Divider,
  InputGroup,
  Select,
  SelectGroup,
  SelectOption,
  SelectVariant,
  TextInput,
  Tooltip,
} from '@patternfly/react-core';
import { SearchIcon, QuestionCircleIcon } from '@patternfly/react-icons';
import styled from 'styled-components';
import { useLocation } from 'react-router-dom';
import { useConfig } from 'contexts/Config';
import getDocsBaseUrl from 'util/getDocsBaseUrl';
import { SearchableKeys } from 'types';
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
  handleIsAnsibleFactsSelected,
  isFilterCleared,
}) {
  const relatedKeys = relatedSearchableKeys.filter(
    (sKey) => !searchableKeys.map(({ key }) => key).includes(sKey)
  );
  const [isPrefixDropdownOpen, setIsPrefixDropdownOpen] = useState(false);
  const [isKeyDropdownOpen, setIsKeyDropdownOpen] = useState(false);
  const [prefixSelection, setPrefixSelection] = useState(null);
  const [lookupSelection, setLookupSelection] = useState(null);
  const [keySelection, setKeySelection] = useState(null);
  const [searchValue, setSearchValue] = useState('');
  const [isTextInputDisabled, setIsTextInputDisabled] = useState(false);
  const { pathname, search } = useLocation();

  useEffect(() => {
    if (keySelection === 'ansible_facts') {
      handleIsAnsibleFactsSelected(true);
      setPrefixSelection(null);
    } else {
      handleIsAnsibleFactsSelected(false);
    }
  }, [keySelection]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (isFilterCleared && keySelection === 'ansible_facts') {
      setIsTextInputDisabled(false);
    }
  }, [isFilterCleared, keySelection]);

  useEffect(() => {
    if (
      (pathname.includes('edit') || pathname.includes('add')) &&
      keySelection === 'ansible_facts' &&
      search.includes('ansible_facts')
    ) {
      setIsTextInputDisabled(true);
    } else {
      setIsTextInputDisabled(false);
    }
  }, [keySelection, pathname, search]);

  const config = useConfig();

  const selectedKey = searchableKeys.find((k) => k.key === keySelection);
  const relatedSearchKeySelected =
    keySelection &&
    relatedSearchableKeys.indexOf(keySelection) > -1 &&
    !selectedKey;
  const lookupKeyType =
    keySelection && !relatedSearchKeySelected ? selectedKey?.type : null;

  useEffect(() => {
    if (relatedSearchKeySelected && keySelection !== 'ansible_facts') {
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
      if (keySelection === 'ansible_facts') {
        const ansibleFactValue = `${actualSearchKey}__${searchValue}`;
        onSearch('host_filter', ansibleFactValue);
      } else {
        onSearch(actualSearchKey, searchValue);
      }
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

  const renderLookupType = () => {
    if (keySelection === 'ansible_facts') return null;

    return relatedSearchKeySelected ? (
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
    );
  };

  const renderTextInput = () => {
    let placeholderText;
    if (keySelection === 'labels' && lookupSelection === 'search') {
      placeholderText = 'e.g. label_1,label_2';
    }

    if (isTextInputDisabled) {
      return (
        <Tooltip
          content={t`Remove the current search related to ansible facts to enable another search using this key.`}
        >
          <TextInput
            data-cy="advanced-search-text-input"
            type="search"
            aria-label={t`Advanced search value input`}
            isDisabled={!keySelection || isTextInputDisabled}
            value={(!keySelection && t`First, select a key`) || searchValue}
            onChange={setSearchValue}
            onKeyDown={handleAdvancedTextKeyDown}
          />
        </Tooltip>
      );
    }

    return (
      <TextInput
        data-cy="advanced-search-text-input"
        type="search"
        aria-label={t`Advanced search value input`}
        isDisabled={!keySelection}
        value={(!keySelection && t`First, select a key`) || searchValue}
        onChange={setSearchValue}
        onKeyDown={handleAdvancedTextKeyDown}
        placeholder={placeholderText}
      />
    );
  };

  const renderLookupSelection = () => {
    if (keySelection === 'ansible_facts') return null;
    return lookupSelection === 'search' ? (
      <Tooltip
        content={t`Set type disabled for related search field fuzzy searches`}
      >
        {renderSetType()}
      </Tooltip>
    ) : (
      renderSetType()
    );
  };

  return (
    <AdvancedGroup>
      {renderLookupSelection()}
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
        isGrouped
        onCreateOption={setKeySelection}
        maxHeight={maxSelectHeight}
        noResultsFoundText={t`No results found`}
      >
        {[
          ...(searchableKeys.length
            ? [
                <SelectGroup key="direct keys" label={t`Direct Keys`}>
                  {searchableKeys.map((k) => (
                    <SelectOption
                      value={k.key}
                      key={k.key}
                      id={`select-option-${k.key}`}
                    >
                      {k.key}
                    </SelectOption>
                  ))}
                </SelectGroup>,
                <Divider key="divider" />,
              ]
            : []),
          ...(relatedKeys.length
            ? [
                <SelectGroup key="related keys" label={t`Related Keys`}>
                  {relatedKeys.map((rKey) => (
                    <SelectOption
                      value={rKey}
                      key={rKey}
                      id={`select-option-${rKey}`}
                    >
                      {rKey}
                    </SelectOption>
                  ))}
                </SelectGroup>,
              ]
            : []),
        ]}
      </Select>
      {renderLookupType()}

      <InputGroup>
        {renderTextInput()}
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
  onSearch: func.isRequired,
  searchableKeys: SearchableKeys,
  relatedSearchableKeys: arrayOf(string),
  maxSelectHeight: string,
  enableNegativeFiltering: bool,
  enableRelatedFuzzyFiltering: bool,
  handleIsAnsibleFactsSelected: func,
};

AdvancedSearch.defaultProps = {
  searchableKeys: [],
  relatedSearchableKeys: [],
  maxSelectHeight: '300px',
  enableNegativeFiltering: true,
  enableRelatedFuzzyFiltering: true,
  handleIsAnsibleFactsSelected: () => {},
};

export default AdvancedSearch;
