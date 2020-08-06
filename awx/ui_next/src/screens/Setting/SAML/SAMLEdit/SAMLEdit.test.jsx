import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import SAMLEdit from './SAMLEdit';

describe('<SAMLEdit />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<SAMLEdit />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('SAMLEdit').length).toBe(1);
  });
});
