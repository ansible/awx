import { mount } from 'enzyme';
import { main } from '../src/index';

const render = template => mount(template);
const data = { custom_logo: 'foo', custom_login_info: '' }

describe('index.jsx', () => {
  test('initialization', async (done) => {
    const isAuthenticated = () => false;
    const getRoot = jest.fn(() => Promise.resolve({ data }));

    const api = { getRoot, isAuthenticated };
    const wrapper = await main(render, api);

    expect(api.getRoot).toHaveBeenCalled();
    expect(wrapper.find('Dashboard')).toHaveLength(0);
    expect(wrapper.find('Login')).toHaveLength(1);

    const { src } = wrapper.find('Login Brand img').props();
    expect(src).toContain(data.custom_logo);

    done();
  });

  test('dashboard is loaded when authenticated', async (done) => {
    const isAuthenticated = () => true;
    const getRoot = jest.fn(() => Promise.resolve({ data }));

    const api = { getRoot, isAuthenticated };
    const wrapper = await main(render, api);

    expect(api.getRoot).toHaveBeenCalled();
    expect(wrapper.find('Dashboard')).toHaveLength(1);
    expect(wrapper.find('Login')).toHaveLength(0);

    done();
  });
});
