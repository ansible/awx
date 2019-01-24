import { mount } from 'enzyme';
import { main, getLanguage } from '../src/index';

const render = template => mount(template);
const data = { custom_logo: 'foo', custom_login_info: '' };

describe('index.jsx', () => {
  test('login loads when unauthenticated', async (done) => {
    const isAuthenticated = () => false;
    const getRoot = jest.fn(() => Promise.resolve({ data }));

    const api = { getRoot, isAuthenticated };
    const wrapper = await main(render, api);

    expect(api.getRoot).toHaveBeenCalled();
    expect(wrapper.find('App')).toHaveLength(0);
    expect(wrapper.find('Login')).toHaveLength(1);

    const { src } = wrapper.find('Login Brand img').props();
    expect(src).toContain(data.custom_logo);

    done();
  });

  test('app loads when authenticated', async (done) => {
    const isAuthenticated = () => true;
    const getRoot = jest.fn(() => Promise.resolve({ data }));

    const api = { getRoot, isAuthenticated };
    const wrapper = await main(render, api);

    expect(api.getRoot).toHaveBeenCalled();
    expect(wrapper.find('App')).toHaveLength(1);
    expect(wrapper.find('Login')).toHaveLength(0);

    wrapper.find('header a').simulate('click');
    wrapper.update();

    expect(wrapper.find('App')).toHaveLength(1);
    expect(wrapper.find('Login')).toHaveLength(0);

    done();
  });

  test('getLanguage returns the expected language code', () => {
    expect(getLanguage({ languages: ['es-US'] })).toEqual('es');
    expect(getLanguage({ languages: ['es-US'], language: 'fr-FR', userLanguage: 'en-US' })).toEqual('es');
    expect(getLanguage({ language: 'fr-FR', userLanguage: 'en-US' })).toEqual('fr');
    expect(getLanguage({ userLanguage: 'en-US' })).toEqual('en');
  });
});
