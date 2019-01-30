import React from 'react';
import { mount } from 'enzyme';
import { I18nProvider } from '@lingui/react';
import Lookup from '../../src/components/Lookup';

let mockData = [{ name: 'foo', id: 1, isChecked: false }];
describe('<Lookup />', () => {
  test('initially renders succesfully', () => {
    mount(
      <Lookup
        lookup_header="Foo Bar"
        onLookupSave={() => { }}
        data={mockData}
        selected={[]}
      />
    );
  });
  test('Opens modal when search icon is clicked', () => {
    const spy = jest.spyOn(Lookup.prototype, 'handleModalToggle');
    const mockSelected = [{ name: 'foo', id: 1 }];
    const wrapper = mount(
      <I18nProvider>
        <Lookup
          lookup_header="Foo Bar"
          onLookupSave={() => { }}
          data={mockData}
          selected={mockSelected}
        />
      </I18nProvider>
    ).find('Lookup');
    expect(spy).not.toHaveBeenCalled();
    expect(wrapper.state('lookupSelectedItems')).toEqual([]);
    const searchItem = wrapper.find('.pf-c-input-group__text#search');
    searchItem.first().simulate('click');
    expect(spy).toHaveBeenCalled();
    expect(wrapper.state('lookupSelectedItems')).toEqual([{
      id: 1,
      name: 'foo'
    }]);
    expect(wrapper.state('isModalOpen')).toEqual(true);
  });
  test('calls "toggleSelected" when a user changes a checkbox', () => {
    const spy = jest.spyOn(Lookup.prototype, 'toggleSelected');
    const wrapper = mount(
      <I18nProvider>
        <Lookup
          lookup_header="Foo Bar"
          onLookupSave={() => { }}
          data={mockData}
          selected={[]}
        />
      </I18nProvider>
    );
    const searchItem = wrapper.find('.pf-c-input-group__text#search');
    searchItem.first().simulate('click');
    wrapper.find('input[type="checkbox"]').simulate('change');
    expect(spy).toHaveBeenCalled();
  });
  test('calls "toggleSelected" when remove icon is clicked', () => {
    const spy = jest.spyOn(Lookup.prototype, 'toggleSelected');
    mockData = [{ name: 'foo', id: 1, isChecked: false }, { name: 'bar', id: 2, isChecked: true }];
    const mockSelected = [{ name: 'foo', id: 1 }, { name: 'bar', id: 2 }];
    const wrapper = mount(
      <I18nProvider>
        <Lookup
          lookup_header="Foo Bar"
          onLookupSave={() => { }}
          data={mockData}
          selected={mockSelected}
        />
      </I18nProvider>
    );
    const removeIcon = wrapper.find('.awx-c-icon--remove').first();
    removeIcon.simulate('click');
    expect(spy).toHaveBeenCalled();
  });
  test('"wrapTags" method properly handles data', () => {
    const spy = jest.spyOn(Lookup.prototype, 'wrapTags');
    mockData = [{ name: 'foo', id: 0, isChecked: false }, { name: 'bar', id: 1, isChecked: false }];
    const wrapper = mount(
      <I18nProvider>
        <Lookup
          lookup_header="Foo Bar"
          onLookupSave={() => { }}
          data={mockData}
          selected={[]}
        />
      </I18nProvider>
    );
    expect(spy).toHaveBeenCalled();
    const pill = wrapper.find('span.awx-c-tag--pill');
    expect(pill).toHaveLength(0);
  });
  test('toggleSelected successfully adds/removes row from lookupSelectedItems state', () => {
    mockData = [{ name: 'foo', id: 1 }];
    const wrapper = mount(
      <I18nProvider>
        <Lookup
          lookup_header="Foo Bar"
          onLookupSave={() => { }}
          data={mockData}
          selected={[]}
        />
      </I18nProvider>
    ).find('Lookup');
    wrapper.instance().toggleSelected({
      id: 1,
      name: 'foo'
    });
    expect(wrapper.state('lookupSelectedItems')).toEqual([{
      id: 1,
      name: 'foo'
    }]);
    wrapper.instance().toggleSelected({
      id: 1,
      name: 'foo'
    });
    expect(wrapper.state('lookupSelectedItems')).toEqual([]);
  });
  test('saveModal calls callback with selected items', () => {
    mockData = [{ name: 'foo', id: 1 }];
    const onLookupSaveFn = jest.fn();
    const wrapper = mount(
      <I18nProvider>
        <Lookup
          lookup_header="Foo Bar"
          onLookupSave={onLookupSaveFn}
          data={mockData}
          selected={[]}
        />
      </I18nProvider>
    ).find('Lookup');
    wrapper.instance().toggleSelected({
      id: 1,
      name: 'foo'
    });
    expect(wrapper.state('lookupSelectedItems')).toEqual([{
      id: 1,
      name: 'foo'
    }]);
    wrapper.instance().saveModal();
    expect(onLookupSaveFn).toHaveBeenCalledWith([{
      id: 1,
      name: 'foo'
    }]);
  });
});
