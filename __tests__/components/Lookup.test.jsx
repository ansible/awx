import React from 'react';
import { mount } from 'enzyme';
import Lookup from '../../src/components/Lookup';
import { I18nProvider } from '@lingui/react';


const mockData = [{ name: 'foo', id: 0, isChecked: false }];
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
    wrapper.find('#search').simulate('click');
    expect(spy).toHaveBeenCalled();
  });
});
