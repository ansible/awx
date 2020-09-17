import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import RADIUSEdit from './RADIUSEdit';

describe('<RADIUSEdit />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<RADIUSEdit />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('RADIUSEdit').length).toBe(1);
  });
});
