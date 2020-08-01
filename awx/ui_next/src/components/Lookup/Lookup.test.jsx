/* eslint-disable react/jsx-pascal-case */
import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import { getQSConfig } from '../../util/qs';
import Lookup from './Lookup';

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

const QS_CONFIG = getQSConfig('test', {});
const TestList = () => <div />;

describe('<Lookup />', () => {
  let wrapper;
  let onChange;

  async function mountWrapper() {
    const mockSelected = [{ name: 'foo', id: 1, url: '/api/v2/item/1' }];
    await act(async () => {
      wrapper = mountWithContexts(
        <Lookup
          id="test"
          multiple
          header="Foo Bar"
          value={mockSelected}
          onChange={onChange}
          qsConfig={QS_CONFIG}
          renderOptionsList={({ state, dispatch, canDelete }) => (
            <TestList
              id="options-list"
              state={state}
              dispatch={dispatch}
              canDelete={canDelete}
            />
          )}
        />
      );
    });
    return wrapper;
  }

  beforeEach(() => {
    onChange = jest.fn();
    document.body.innerHTML = '';
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('should render succesfully', async () => {
    wrapper = await mountWrapper();
    expect(wrapper.find('Lookup')).toHaveLength(1);
  });

  test('should show selected items', async () => {
    wrapper = await mountWrapper();
    expect(wrapper.find('Lookup')).toHaveLength(1);
    await checkInputTagValues(wrapper, ['foo']);
  });

  test('should open and close modal', async () => {
    wrapper = await mountWrapper();
    checkRootElementNotPresent('body div[role="dialog"]');
    wrapper.find('button[aria-label="Search"]').simulate('click');
    checkRootElementPresent('body div[role="dialog"]');
    const list = wrapper.find('TestList');
    expect(list).toHaveLength(1);
    expect(list.prop('state')).toEqual({
      selectedItems: [{ id: 1, name: 'foo', url: '/api/v2/item/1' }],
      value: [{ id: 1, name: 'foo', url: '/api/v2/item/1' }],
      multiple: true,
      isModalOpen: true,
      required: false,
    });
    expect(list.prop('dispatch')).toBeTruthy();
    expect(list.prop('canDelete')).toEqual(true);
    wrapper
      .find('Modal button')
      .findWhere(e => e.text() === 'Cancel')
      .first()
      .simulate('click');
    checkRootElementNotPresent('body div[role="dialog"]');
  });

  test('should remove item when X button clicked', async () => {
    wrapper = await mountWrapper();
    await checkInputTagValues(wrapper, ['foo']);
    wrapper
      .find('Lookup InputGroup Chip')
      .findWhere(el => el.text() === 'foo')
      .first()
      .invoke('onClick')();
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith([]);
  });

  test('should pass canDelete false if required single select', async () => {
    await act(async () => {
      const mockSelected = { name: 'foo', id: 1, url: '/api/v2/item/1' };
      wrapper = mountWithContexts(
        <Lookup
          id="test"
          header="Foo Bar"
          required
          value={mockSelected}
          onChange={onChange}
          qsConfig={QS_CONFIG}
          renderOptionsList={({ state, dispatch, canDelete }) => (
            <TestList
              id="options-list"
              state={state}
              dispatch={dispatch}
              canDelete={canDelete}
            />
          )}
        />
      );
    });
    wrapper.find('button[aria-label="Search"]').simulate('click');
    const list = wrapper.find('TestList');
    expect(list.prop('canDelete')).toEqual(false);
  });

  test('should be disabled while isLoading is true', async () => {
    const mockSelected = [{ name: 'foo', id: 1, url: '/api/v2/item/1' }];
    wrapper = mountWithContexts(
      <Lookup
        id="test"
        multiple
        header="Foo Bar"
        value={mockSelected}
        onChange={onChange}
        qsConfig={QS_CONFIG}
        isLoading
        renderOptionsList={({ state, dispatch, canDelete }) => (
          <TestList
            id="options-list"
            state={state}
            dispatch={dispatch}
            canDelete={canDelete}
          />
        )}
      />
    );
    checkRootElementNotPresent('body div[role="dialog"]');
    const button = wrapper.find('button[aria-label="Search"]');
    expect(button.prop('disabled')).toEqual(true);
  });
});
