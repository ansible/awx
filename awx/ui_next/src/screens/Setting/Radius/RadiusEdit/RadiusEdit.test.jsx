import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import RadiusEdit from './RadiusEdit';

describe('<RadiusEdit />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<RadiusEdit />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('RadiusEdit').length).toBe(1);
  });
});
