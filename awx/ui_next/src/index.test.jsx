import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import { main } from './index';

const render = template => mount(<MemoryRouter>{template}</MemoryRouter>);

describe('index.jsx', () => {
  test('index.jsx loads without issue', () => {
    const wrapper = main(render);
    expect(wrapper.find('RootProvider')).toHaveLength(1);
  });
});
