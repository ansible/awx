import 'styled-components/macro';
import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Button,
  ButtonVariant,
  InputGroup,
  Select,
  SelectOption,
  SelectVariant,
  TextInput,
} from '@patternfly/react-core';
import { SearchIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

const AdvancedGroup = styled.div`
  display: flex;

  @media (max-width: 991px) {
    display: grid;
    grid-gap: var(--pf-c-toolbar__expandable-content--m-expanded--GridRowGap);
  }
`;

function AdvancedSearch({
  i18n,
  onSearch,
  searchableKeys,
  relatedSearchableKeys,
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
        aria-label={i18n._(t`Set type select`)}
        className="setTypeSelect"
        variant={SelectVariant.typeahead}
        typeAheadAriaLabel={i18n._(t`Set type typeahead`)}
        onToggle={setIsPrefixDropdownOpen}
        onSelect={(event, selection) => setPrefixSelection(selection)}
        onClear={() => setPrefixSelection(null)}
        selections={prefixSelection}
        isOpen={isPrefixDropdownOpen}
        placeholderText={i18n._(t`Set type`)}
        maxHeight="500px"
      >
        <SelectOption
          key="and"
          value="and"
          description={i18n._(
            t`Returns results that satisfy this one as well as other filters.  This is the default set type if nothing is selected.`
          )}
        />
        <SelectOption
          key="or"
          value="or"
          description={i18n._(
            t`Returns results that satisfy this one or any other filters.`
          )}
        />
        <SelectOption
          key="not"
          value="not"
          description={i18n._(
            t`Returns results that have values other than this one as well as other filters.`
          )}
        />
      </Select>
      <Select
        aria-label={i18n._(t`Key select`)}
        className="keySelect"
        variant={SelectVariant.typeahead}
        typeAheadAriaLabel={i18n._(t`Key typeahead`)}
        onToggle={setIsKeyDropdownOpen}
        onSelect={(event, selection) => setKeySelection(selection)}
        onClear={() => setKeySelection(null)}
        selections={keySelection}
        isOpen={isKeyDropdownOpen}
        placeholderText={i18n._(t`Key`)}
        isCreatable
        onCreateOption={setKeySelection}
        maxHeight="500px"
      >
        {allKeys.map(optionKey => (
          <SelectOption key={optionKey} value={optionKey}>
            {optionKey}
          </SelectOption>
        ))}
      </Select>
      <Select
        aria-label={i18n._(t`Lookup select`)}
        className="lookupSelect"
        variant={SelectVariant.typeahead}
        typeAheadAriaLabel={i18n._(t`Lookup typeahead`)}
        onToggle={setIsLookupDropdownOpen}
        onSelect={(event, selection) => setLookupSelection(selection)}
        onClear={() => setLookupSelection(null)}
        selections={lookupSelection}
        isOpen={isLookupDropdownOpen}
        placeholderText={i18n._(t`Lookup type`)}
        maxHeight="500px"
      >
        <SelectOption
          key="exact"
          value="exact"
          description={i18n._(
            t`Exact match (default lookup if not specified).`
          )}
        />
        <SelectOption
          key="iexact"
          value="iexact"
          description={i18n._(t`Case-insensitive version of exact.`)}
        />
        <SelectOption
          key="contains"
          value="contains"
          description={i18n._(t`Field contains value.`)}
        />
        <SelectOption
          key="icontains"
          value="icontains"
          description={i18n._(t`Case-insensitive version of contains`)}
        />
        <SelectOption
          key="startswith"
          value="startswith"
          description={i18n._(t`Field starts with value.`)}
        />
        <SelectOption
          key="istartswith"
          value="istartswith"
          description={i18n._(t`Case-insensitive version of startswith.`)}
        />
        <SelectOption
          key="endswith"
          value="endswith"
          description={i18n._(t`Field ends with value.`)}
        />
        <SelectOption
          key="iendswith"
          value="iendswith"
          description={i18n._(t`Case-insensitive version of endswith.`)}
        />
        <SelectOption
          key="regex"
          value="regex"
          description={i18n._(t`Field matches the given regular expression.`)}
        />
        <SelectOption
          key="iregex"
          value="iregex"
          description={i18n._(t`Case-insensitive version of regex.`)}
        />
        <SelectOption
          key="gt"
          value="gt"
          description={i18n._(t`Greater than comparison.`)}
        />
        <SelectOption
          key="gte"
          value="gte"
          description={i18n._(t`Greater than or equal to comparison.`)}
        />
        <SelectOption
          key="lt"
          value="lt"
          description={i18n._(t`Less than comparison.`)}
        />
        <SelectOption
          key="lte"
          value="lte"
          description={i18n._(t`Less than or equal to comparison.`)}
        />
        <SelectOption
          key="isnull"
          value="isnull"
          description={i18n._(
            t`Check whether the given field or related object is null; expects a boolean value.`
          )}
        />
        <SelectOption
          key="in"
          value="in"
          description={i18n._(
            t`Check whether the given field's value is present in the list provided; expects a comma-separated list of items.`
          )}
        />
      </Select>
      <InputGroup>
        <TextInput
          type="search"
          aria-label={i18n._(t`Advanced search value input`)}
          isDisabled={!keySelection}
          value={
            (!keySelection && i18n._(t`First, select a key`)) || searchValue
          }
          onChange={setSearchValue}
          onKeyDown={handleAdvancedTextKeyDown}
        />
        <div css={!searchValue && `cursor:not-allowed`}>
          <Button
            variant={ButtonVariant.control}
            isDisabled={!searchValue}
            aria-label={i18n._(t`Search submit button`)}
            onClick={handleAdvancedSearch}
          >
            <SearchIcon />
          </Button>
        </div>
      </InputGroup>
    </AdvancedGroup>
  );
}

AdvancedSearch.propTypes = {
  onSearch: PropTypes.func.isRequired,
  searchableKeys: PropTypes.arrayOf(PropTypes.string),
  relatedSearchableKeys: PropTypes.arrayOf(PropTypes.string),
};

AdvancedSearch.defaultProps = {
  searchableKeys: [],
  relatedSearchableKeys: [],
};

export default withI18n()(AdvancedSearch);
