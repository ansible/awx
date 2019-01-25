import React from 'react';
import { mount } from 'enzyme';
import { I18nProvider } from '@lingui/react';
import Lookup from '../../src/components/Lookup';

let mockData = [{ name: 'foo', id: 0, isChecked: false }];
describe('<Lookup />', () => {
  test('initially renders succesfully', () => {
    mount(
      <Lookup
        lookup_header="Foo Bar"
        lookupChange={() => { }}
        data={mockData}
      />
    );
  });
  test('calls "onLookup" when search icon is clicked', () => {
    const spy = jest.spyOn(Lookup.prototype, 'onLookup');
    const wrapper = mount(
      <I18nProvider>
        <Lookup
          lookup_header="Foo Bar"
          lookupChange={() => { }}
          data={mockData}
        />
      </I18nProvider>
    );
    expect(spy).not.toHaveBeenCalled();
    debugger;
    const searchItem = wrapper.find('.pf-c-input-group__text#search');
    searchItem.first().simulate('click');
    expect(spy).toHaveBeenCalled();
  });
  test('calls "onChecked" when a user changes a checkbox', () => {
    const spy = jest.spyOn(Lookup.prototype, 'onChecked');
    const wrapper = mount(
      <I18nProvider>
        <Lookup
          lookup_header="Foo Bar"
          lookupChange={() => { }}
          data={mockData}
        />
      </I18nProvider>
    );
    debugger;
    const searchItem = wrapper.find('.pf-c-input-group__text#search');
    searchItem.first().simulate('click');
    wrapper.find('input[type="checkbox"]').simulate('change');
    expect(spy).toHaveBeenCalled();
  });
  test('calls "onRemove" when remove icon is clicked', () => {
    const spy = jest.spyOn(Lookup.prototype, 'onRemove');
    mockData = [{ name: 'foo', id: 0, isChecked: false }, { name: 'bar', id: 1, isChecked: true }];
    const wrapper = mount(
      <I18nProvider>
        <Lookup
          lookup_header="Foo Bar"
          lookupChange={() => { }}
          data={mockData}
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
          lookupChange={() => { }}
          data={mockData}
        />
      </I18nProvider>
    );
    expect(spy).toHaveBeenCalled();
    const pill = wrapper.find('span.awx-c-tag--pill');
    expect(pill).toHaveLength(0);
  });
});
