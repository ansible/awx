/* eslint-disable react/jsx-pascal-case */
import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import Lookup, { _Lookup } from './Lookup';

let mockData = [{ name: 'foo', id: 1, isChecked: false }];
const mockColumns = [{ name: 'Name', key: 'name', isSortable: true }];

/**
 * Check that an element is present on the document body
 * @param {selector} query selector
 */
function checkRootElementPresent(selector) {
  const queryResult = global.document.querySelector(selector);
  expect(queryResult).not.toEqual(null);
}

/**
 * Check that an element isn't present on the document body
 * @param {selector} query selector
 */
function checkRootElementNotPresent(selector) {
  const queryResult = global.document.querySelector(selector);
  expect(queryResult).toEqual(null);
}

/**
 * Check lookup input group tags for expected values
 * @param {wrapper} enzyme wrapper instance
 * @param {expected} array of expected tag values
 */
async function checkInputTagValues(wrapper, expected) {
  checkRootElementNotPresent('body div[role="dialog"]');
  // check input group chip values
  const chips = await waitForElement(
    wrapper,
    'Lookup InputGroup Chip span',
    el => el.length === expected.length
  );
  expect(chips).toHaveLength(expected.length);
  chips.forEach((el, index) => {
    expect(el.text()).toEqual(expected[index]);
  });
}

/**
 * Check lookup modal list for expected values
 * @param {wrapper} enzyme wrapper instance
 * @param {expected} array of [selected, text] pairs describing
 * the expected visible state of the modal data list
 */
async function checkModalListValues(wrapper, expected) {
  // fail if modal isn't actually visible
  checkRootElementPresent('body div[role="dialog"]');
  // check list item values
  const rows = await waitForElement(
    wrapper,
    'DataListItemRow',
    el => el.length === expected.length
  );
  expect(rows).toHaveLength(expected.length);
  rows.forEach((el, index) => {
    const [expectedChecked, expectedText] = expected[index];
    expect(expectedText).toEqual(el.text());
    expect(expectedChecked).toEqual(el.find('input').props().checked);
  });
}

/**
 * Check lookup modal selection tags for expected values
 * @param {wrapper} enzyme wrapper instance
 * @param {expected} array of expected tag values
 */
async function checkModalTagValues(wrapper, expected) {
  // fail if modal isn't actually visible
  checkRootElementPresent('body div[role="dialog"]');
  // check modal chip values
  const chips = await waitForElement(
    wrapper,
    'Modal Chip span',
    el => el.length === expected.length
  );
  expect(chips).toHaveLength(expected.length);
  chips.forEach((el, index) => {
    expect(el.text()).toEqual(expected[index]);
  });
}

describe('<Lookup multiple/>', () => {
  let wrapper;
  let onChange;

  beforeEach(() => {
    const mockSelected = [{ name: 'foo', id: 1, url: '/api/v2/item/1' }];
    onChange = jest.fn();
    document.body.innerHTML = '';
    wrapper = mountWithContexts(
      <Lookup
        multiple
        lookupHeader="Foo Bar"
        name="foobar"
        value={mockSelected}
        onLookupSave={onChange}
        getItems={() => ({
          data: {
            count: 2,
            results: [
              ...mockSelected,
              { name: 'bar', id: 2, url: '/api/v2/item/2' },
            ],
          },
        })}
        columns={mockColumns}
        sortedColumnKey="name"
      />
    );
  });

  test('Initially renders succesfully', () => {
    expect(wrapper.find('Lookup')).toHaveLength(1);
  });

  test('Expected items are shown', async done => {
    expect(wrapper.find('Lookup')).toHaveLength(1);
    await checkInputTagValues(wrapper, ['foo']);
    done();
  });

  test('Open and close modal', async done => {
    checkRootElementNotPresent('body div[role="dialog"]');
    wrapper.find('button[aria-label="Search"]').simulate('click');
    checkRootElementPresent('body div[role="dialog"]');
    // This check couldn't pass unless api response was formatted properly
    await checkModalListValues(wrapper, [[true, 'foo'], [false, 'bar']]);
    wrapper.find('Modal button[aria-label="Close"]').simulate('click');
    checkRootElementNotPresent('body div[role="dialog"]');
    wrapper.find('button[aria-label="Search"]').simulate('click');
    checkRootElementPresent('body div[role="dialog"]');
    wrapper
      .find('Modal button')
      .findWhere(e => e.text() === 'Cancel')
      .first()
      .simulate('click');
    checkRootElementNotPresent('body div[role="dialog"]');
    done();
  });

  test('Add item with checkbox then save', async done => {
    wrapper.find('button[aria-label="Search"]').simulate('click');
    await checkModalListValues(wrapper, [[true, 'foo'], [false, 'bar']]);
    wrapper
      .find('DataListItemRow')
      .findWhere(el => el.text() === 'bar')
      .find('input[type="checkbox"]')
      .simulate('change');
    await checkModalListValues(wrapper, [[true, 'foo'], [true, 'bar']]);
    wrapper
      .find('Modal button')
      .findWhere(e => e.text() === 'Save')
      .first()
      .simulate('click');
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange.mock.calls[0][0].map(({ name }) => name)).toEqual([
      'foo',
      'bar',
    ]);
    done();
  });

  test('Add item with checkbox then cancel', async done => {
    wrapper.find('button[aria-label="Search"]').simulate('click');
    await checkModalListValues(wrapper, [[true, 'foo'], [false, 'bar']]);
    wrapper
      .find('DataListItemRow')
      .findWhere(el => el.text() === 'bar')
      .find('input[type="checkbox"]')
      .simulate('change');
    await checkModalListValues(wrapper, [[true, 'foo'], [true, 'bar']]);
    wrapper
      .find('Modal button')
      .findWhere(e => e.text() === 'Cancel')
      .first()
      .simulate('click');
    expect(onChange).toHaveBeenCalledTimes(0);
    await checkInputTagValues(wrapper, ['foo']);
    done();
  });

  test('Remove item with checkbox', async done => {
    wrapper.find('button[aria-label="Search"]').simulate('click');
    await checkModalListValues(wrapper, [[true, 'foo'], [false, 'bar']]);
    await checkModalTagValues(wrapper, ['foo']);
    wrapper
      .find('DataListItemRow')
      .findWhere(el => el.text() === 'foo')
      .find('input[type="checkbox"]')
      .simulate('change');
    await checkModalListValues(wrapper, [[false, 'foo'], [false, 'bar']]);
    await checkModalTagValues(wrapper, []);
    done();
  });

  test('Remove item with selected icon button', async done => {
    wrapper.find('button[aria-label="Search"]').simulate('click');
    await checkModalListValues(wrapper, [[true, 'foo'], [false, 'bar']]);
    await checkModalTagValues(wrapper, ['foo']);
    wrapper
      .find('Modal Chip')
      .findWhere(el => el.text() === 'foo')
      .first()
      .find('button')
      .simulate('click');
    await checkModalListValues(wrapper, [[false, 'foo'], [false, 'bar']]);
    await checkModalTagValues(wrapper, []);
    done();
  });

  test('Remove item with input group button', async done => {
    await checkInputTagValues(wrapper, ['foo']);
    wrapper
      .find('Lookup InputGroup Chip')
      .findWhere(el => el.text() === 'foo')
      .first()
      .find('button')
      .simulate('click');
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith([], 'foobar');
    done();
  });
});

describe('<Lookup />', () => {
  let wrapper;
  let onChange;

  beforeEach(() => {
    const mockSelected = { name: 'foo', id: 1, url: '/api/v2/item/1' };
    onChange = jest.fn();
    document.body.innerHTML = '';
    wrapper = mountWithContexts(
      <Lookup
        lookupHeader="Foo Bar"
        name="foobar"
        value={mockSelected}
        onLookupSave={onChange}
        getItems={() => ({
          data: {
            count: 2,
            results: [
              mockSelected,
              { name: 'bar', id: 2, url: '/api/v2/item/2' },
            ],
          },
        })}
        columns={mockColumns}
        sortedColumnKey="name"
      />
    );
  });

  test('Initially renders succesfully', () => {
    expect(wrapper.find('Lookup')).toHaveLength(1);
  });

  test('Expected items are shown', async done => {
    expect(wrapper.find('Lookup')).toHaveLength(1);
    await checkInputTagValues(wrapper, ['foo']);
    done();
  });

  test('Open and close modal', async done => {
    checkRootElementNotPresent('body div[role="dialog"]');
    wrapper.find('button[aria-label="Search"]').simulate('click');
    checkRootElementPresent('body div[role="dialog"]');
    // This check couldn't pass unless api response was formatted properly
    await checkModalListValues(wrapper, [[true, 'foo'], [false, 'bar']]);
    wrapper.find('Modal button[aria-label="Close"]').simulate('click');
    checkRootElementNotPresent('body div[role="dialog"]');
    wrapper.find('button[aria-label="Search"]').simulate('click');
    checkRootElementPresent('body div[role="dialog"]');
    wrapper
      .find('Modal button')
      .findWhere(e => e.text() === 'Cancel')
      .first()
      .simulate('click');
    checkRootElementNotPresent('body div[role="dialog"]');
    done();
  });

  test('Change selected item with radio control then save', async done => {
    wrapper.find('button[aria-label="Search"]').simulate('click');
    await checkModalListValues(wrapper, [[true, 'foo'], [false, 'bar']]);
    await checkModalTagValues(wrapper, ['foo']);
    wrapper
      .find('DataListItemRow')
      .findWhere(el => el.text() === 'bar')
      .find('input[type="radio"]')
      .simulate('change');
    await checkModalListValues(wrapper, [[false, 'foo'], [true, 'bar']]);
    await checkModalTagValues(wrapper, ['bar']);
    wrapper
      .find('Modal button')
      .findWhere(e => e.text() === 'Save')
      .first()
      .simulate('click');
    expect(onChange).toHaveBeenCalledTimes(1);
    const [[{ name }]] = onChange.mock.calls;
    expect(name).toEqual('bar');
    done();
  });

  test('Change selected item with checkbox then cancel', async done => {
    wrapper.find('button[aria-label="Search"]').simulate('click');
    await checkModalListValues(wrapper, [[true, 'foo'], [false, 'bar']]);
    await checkModalTagValues(wrapper, ['foo']);
    wrapper
      .find('DataListItemRow')
      .findWhere(el => el.text() === 'bar')
      .find('input[type="radio"]')
      .simulate('change');
    await checkModalListValues(wrapper, [[false, 'foo'], [true, 'bar']]);
    await checkModalTagValues(wrapper, ['bar']);
    wrapper
      .find('Modal button')
      .findWhere(e => e.text() === 'Cancel')
      .first()
      .simulate('click');
    expect(onChange).toHaveBeenCalledTimes(0);
    done();
  });

  test('should re-fetch data when URL params change', async done => {
    mockData = [{ name: 'foo', id: 1, isChecked: false }];
    const history = createMemoryHistory({
      initialEntries: ['/organizations/add'],
    });
    const getItems = jest.fn();
    const LookupWrapper = mountWithContexts(
      <_Lookup
        multiple
        name="foo"
        lookupHeader="Foo Bar"
        onLookupSave={() => {}}
        value={mockData}
        columns={mockColumns}
        sortedColumnKey="name"
        getItems={getItems}
        location={{ history }}
        i18n={{ _: val => val.toString() }}
      />
    );
    expect(getItems).toHaveBeenCalledTimes(1);
    history.push('organizations/add?page=2');
    LookupWrapper.setProps({
      location: { history },
    });
    LookupWrapper.update();
    expect(getItems).toHaveBeenCalledTimes(2);
    done();
  });

  test('should clear its query params when closed', async () => {
    mockData = [{ name: 'foo', id: 1, isChecked: false }];
    const history = createMemoryHistory({
      initialEntries: ['/organizations/add?inventory.name=foo&bar=baz'],
    });
    wrapper = mountWithContexts(
      <_Lookup
        multiple
        name="foo"
        lookupHeader="Foo Bar"
        onLookupSave={() => {}}
        value={mockData}
        columns={mockColumns}
        sortedColumnKey="name"
        getItems={() => {}}
        location={{ history }}
        history={history}
        qsNamespace="inventory"
        i18n={{ _: val => val.toString() }}
      />
    );
    wrapper
      .find('InputGroup Button')
      .at(0)
      .invoke('onClick')();
    wrapper.find('Modal').invoke('onClose')();
    expect(history.location.search).toEqual('?bar=baz');
  });
});
