/* eslint-disable react/jsx-pascal-case */
import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import Lookup, { _Lookup } from './Lookup';

let mockData = [{ name: 'foo', id: 1, isChecked: false }];
const mockColumns = [{ name: 'Name', key: 'name', isSortable: true }];
describe('<Lookup />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(
      <Lookup
        lookupHeader="Foo Bar"
        name="fooBar"
        value={mockData}
        onLookupSave={() => {}}
        getItems={() => {}}
        columns={mockColumns}
        sortedColumnKey="name"
      />
    );
  });

  test('API response is formatted properly', done => {
    const wrapper = mountWithContexts(
      <Lookup
        lookupHeader="Foo Bar"
        name="fooBar"
        value={mockData}
        onLookupSave={() => {}}
        getItems={() => ({
          data: { results: [{ name: 'test instance', id: 1 }] },
        })}
        columns={mockColumns}
        sortedColumnKey="name"
      />
    ).find('Lookup');

    setImmediate(() => {
      expect(wrapper.state().results).toEqual([
        { id: 1, name: 'test instance' },
      ]);
      done();
    });
  });

  test('Opens modal when search icon is clicked', () => {
    const spy = jest.spyOn(_Lookup.prototype, 'handleModalToggle');
    const mockSelected = [{ name: 'foo', id: 1 }];
    const wrapper = mountWithContexts(
      <Lookup
        id="search"
        lookupHeader="Foo Bar"
        name="fooBar"
        value={mockSelected}
        onLookupSave={() => {}}
        getItems={() => {}}
        columns={mockColumns}
        sortedColumnKey="name"
      />
    ).find('Lookup');
    expect(spy).not.toHaveBeenCalled();
    expect(wrapper.state('lookupSelectedItems')).toEqual(mockSelected);
    const searchItem = wrapper.find('button[aria-label="Search"]');
    searchItem.first().simulate('click');
    expect(spy).toHaveBeenCalled();
    expect(wrapper.state('lookupSelectedItems')).toEqual([
      {
        id: 1,
        name: 'foo',
      },
    ]);
    expect(wrapper.state('isModalOpen')).toEqual(true);
  });

  test('calls "toggleSelected" when a user changes a checkbox', done => {
    const spy = jest.spyOn(_Lookup.prototype, 'toggleSelected');
    const mockSelected = [{ name: 'foo', id: 1 }];
    const data = {
      results: [{ name: 'test instance', id: 1, url: '/foo' }],
      count: 1,
    };
    const wrapper = mountWithContexts(
      <Lookup
        id="search"
        lookupHeader="Foo Bar"
        name="fooBar"
        value={mockSelected}
        onLookupSave={() => {}}
        getItems={() => ({ data })}
        columns={mockColumns}
        sortedColumnKey="name"
      />
    );
    setImmediate(() => {
      const searchItem = wrapper.find('button[aria-label="Search"]');
      searchItem.first().simulate('click');
      wrapper.find('input[type="checkbox"]').simulate('change');
      expect(spy).toHaveBeenCalled();
      done();
    });
  });

  test('calls "toggleSelected" when remove icon is clicked', () => {
    const spy = jest.spyOn(_Lookup.prototype, 'toggleSelected');
    mockData = [{ name: 'foo', id: 1 }, { name: 'bar', id: 2 }];
    const data = {
      results: [{ name: 'test instance', id: 1, url: '/foo' }],
      count: 1,
    };
    const wrapper = mountWithContexts(
      <Lookup
        id="search"
        lookupHeader="Foo Bar"
        name="fooBar"
        value={mockData}
        onLookupSave={() => {}}
        getItems={() => ({ data })}
        columns={mockColumns}
        sortedColumnKey="name"
      />
    );
    const removeIcon = wrapper.find('button[aria-label="close"]').first();
    removeIcon.simulate('click');
    expect(spy).toHaveBeenCalled();
  });

  test('renders chips from prop value', () => {
    mockData = [{ name: 'foo', id: 0 }, { name: 'bar', id: 1 }];
    const wrapper = mountWithContexts(
      <Lookup
        lookupHeader="Foo Bar"
        onLookupSave={() => {}}
        value={mockData}
        selected={[]}
        getItems={() => {}}
        columns={mockColumns}
        sortedColumnKey="name"
      />
    ).find('Lookup');
    const chip = wrapper.find('.pf-c-chip');
    expect(chip).toHaveLength(2);
  });

  test('toggleSelected successfully adds/removes row from lookupSelectedItems state', () => {
    mockData = [];
    const wrapper = mountWithContexts(
      <Lookup
        lookupHeader="Foo Bar"
        onLookupSave={() => {}}
        value={mockData}
        getItems={() => {}}
        columns={mockColumns}
        sortedColumnKey="name"
      />
    ).find('Lookup');
    wrapper.instance().toggleSelected({
      id: 1,
      name: 'foo',
    });
    expect(wrapper.state('lookupSelectedItems')).toEqual([
      {
        id: 1,
        name: 'foo',
      },
    ]);
    wrapper.instance().toggleSelected({
      id: 1,
      name: 'foo',
    });
    expect(wrapper.state('lookupSelectedItems')).toEqual([]);
  });

  test('saveModal calls callback with selected items', () => {
    mockData = [];
    const onLookupSaveFn = jest.fn();
    const wrapper = mountWithContexts(
      <Lookup
        lookupHeader="Foo Bar"
        name="fooBar"
        value={mockData}
        onLookupSave={onLookupSaveFn}
        getItems={() => {}}
        sortedColumnKey="name"
      />
    ).find('Lookup');
    wrapper.instance().toggleSelected({
      id: 1,
      name: 'foo',
    });
    expect(wrapper.state('lookupSelectedItems')).toEqual([
      {
        id: 1,
        name: 'foo',
      },
    ]);
    wrapper.instance().saveModal();
    expect(onLookupSaveFn).toHaveBeenCalledWith(
      [
        {
          id: 1,
          name: 'foo',
        },
      ],
      'fooBar'
    );
  });

  test('should re-fetch data when URL params change', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/organizations/add'],
    });
    const getItems = jest.fn();
    const wrapper = mountWithContexts(
      <_Lookup
        lookupHeader="Foo Bar"
        onLookupSave={() => {}}
        value={mockData}
        selected={[]}
        columns={mockColumns}
        sortedColumnKey="name"
        getItems={getItems}
        handleHttpError={() => {}}
        location={{ history }}
        i18n={{ _: val => val.toString() }}
      />
    );

    expect(getItems).toHaveBeenCalledTimes(1);
    history.push('organizations/add?page=2');
    wrapper.setProps({
      location: { history },
    });
    wrapper.update();
    expect(getItems).toHaveBeenCalledTimes(2);
  });
});
