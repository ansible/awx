import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import GitHubDetail from './GitHubDetail';

describe('<GitHubDetail />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<GitHubDetail />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('GitHubDetail').length).toBe(1);
  });
});
