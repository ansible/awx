import { mount } from 'enzyme';
import { main } from '../src/index';

const render = template => mount(template);

describe('index.jsx', () => {
  test('index.jsx loads without issue', () => {
    const wrapper = main(render);
    expect(wrapper.find('RootProvider')).toHaveLength(1);
  });
});
