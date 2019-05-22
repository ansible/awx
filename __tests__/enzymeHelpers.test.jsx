import React, { Component } from 'react';
import { Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { mountWithContexts, waitForElement } from './enzymeHelpers';
import { Config } from '../src/contexts/Config';
import { withNetwork } from '../src/contexts/Network';
import { withRootDialog } from '../src/contexts/RootDialog';

describe('mountWithContexts', () => {
  describe('injected I18nProvider', () => {
    test('should mount and render', () => {
      const Child = withI18n()(({ i18n }) => (
        <div>
          <span>{i18n._(t`Text content`)}</span>
        </div>
      ));
      const wrapper = mountWithContexts(<Child />);
      expect(wrapper.find('div')).toMatchSnapshot();
    });

    test('should mount and render deeply nested consumer', () => {
      const Child = withI18n()(({ i18n }) => (
        <div>{i18n._(t`Text content`)}</div>
      ));
      const Parent = () => (<Child />);
      const wrapper = mountWithContexts(<Parent />);
      expect(wrapper.find('Parent')).toMatchSnapshot();
    });
  });

  describe('injected Router', () => {
    it('should mount and render', () => {
      const wrapper = mountWithContexts(
        <div>
          <Link to="/">home</Link>
        </div>
      );

      expect(wrapper.find('div')).toMatchSnapshot();
    });

    it('should mount and render with stubbed context', () => {
      const context = {
        router: {
          history: {
            push: jest.fn(),
            replace: jest.fn(),
            createHref: jest.fn(),
          },
          route: {
            location: {},
            match: {}
          }
        }
      };
      const wrapper = mountWithContexts(
        (
          <div>
            <Link to="/">home</Link>
          </div>
        ),
        { context }
      );

      const link = wrapper.find('Link');
      expect(link).toHaveLength(1);
      link.simulate('click', { button: 0 });
      wrapper.update();

      expect(context.router.history.push).toHaveBeenCalledWith('/');
    });
  });

  describe('injected ConfigProvider', () => {
    it('should mount and render with default values', () => {
      const Foo = () => (
        <Config>
          {value => (
            <div>
              {value.custom_virtualenvs[0]}
              {value.version}
            </div>
          )}
        </Config>
      );
      const wrapper = mountWithContexts(<Foo />);
      expect(wrapper.find('Foo')).toMatchSnapshot();
    });

    it('should mount and render with custom Config value', () => {
      const config = {
        custom_virtualenvs: ['Fizz', 'Buzz'],
        version: '1.1',
      };
      const Foo = () => (
        <Config>
          {value => (
            <div>
              {value.custom_virtualenvs[0]}
              {value.version}
            </div>
          )}
        </Config>
      );
      const wrapper = mountWithContexts(
        <Foo />,
        { context: { config } }
      );
      expect(wrapper.find('Foo')).toMatchSnapshot();
    });
  });

  describe('injected Network', () => {
    it('should mount and render', () => {
      const Foo = () => (
        <div>test</div>
      );
      const Bar = withNetwork(Foo);
      const wrapper = mountWithContexts(<Bar />);
      expect(wrapper.find('Foo')).toMatchSnapshot();
    });

    it('should mount and render with stubbed api', () => {
      const network = {
        api: {
          getFoo: jest.fn().mockReturnValue('foo value'),
        },
      };
      const Foo = ({ api }) => (
        <div>{api.getFoo()}</div>
      );
      const Bar = withNetwork(Foo);
      const wrapper = mountWithContexts(<Bar />, { context: { network } });
      expect(network.api.getFoo).toHaveBeenCalledTimes(1);
      expect(wrapper.find('div').text()).toEqual('foo value');
    });
  });

  describe('injected root dialog', () => {
    it('should mount and render', () => {
      const Foo = ({ title, setRootDialogMessage }) => (
        <div>
          <span>{title}</span>
          <button
            type="button"
            onClick={() => setRootDialogMessage({ title: 'error' })}
          >
            click
          </button>
        </div>
      );
      const Bar = withRootDialog(Foo);
      const wrapper = mountWithContexts(<Bar />);

      expect(wrapper.find('span').text()).toEqual('');
      wrapper.find('button').simulate('click');
      wrapper.update();
      expect(wrapper.find('span').text()).toEqual('error');
    });

    it('should mount and render with stubbed value', () => {
      const dialog = {
        title: 'this be the title',
        setRootDialogMessage: jest.fn(),
      };
      const Foo = ({ title, setRootDialogMessage }) => (
        <div>
          <span>{title}</span>
          <button
            type="button"
            onClick={() => setRootDialogMessage('error')}
          >
            click
          </button>
        </div>
      );
      const Bar = withRootDialog(Foo);
      const wrapper = mountWithContexts(<Bar />, { context: { dialog } });

      expect(wrapper.find('span').text()).toEqual('this be the title');
      wrapper.find('button').simulate('click');
      expect(dialog.setRootDialogMessage).toHaveBeenCalledWith('error');
    });
  });

  it('should set props on wrapped component', () => {
    function TestComponent ({ text }) {
      return (<div>{text}</div>);
    }

    const wrapper = mountWithContexts(
      <TestComponent text="foo" />
    );
    expect(wrapper.find('div').text()).toEqual('foo');
    wrapper.setProps({
      text: 'bar'
    });
    expect(wrapper.find('div').text()).toEqual('bar');
  });
});

/**
 * This is a fixture for testing async components. It renders a div
 * after a short amount of time.
 */
class TestAsyncComponent extends Component {
  constructor (props) {
    super(props);
    this.state = { displayElement: false };
  }

  componentDidMount () {
    setTimeout(() => {
      this.setState({ displayElement: true });
    }, 1000);
  }

  render () {
    const { displayElement } = this.state;
    if (displayElement) {
      return (<div id="test-async-component" />);
    }
    return null;
  }
}

describe('waitForElement', () => {
  it('waits for the element and returns it', async (done) => {
    const selector = '#test-async-component';
    const wrapper = mountWithContexts(<TestAsyncComponent />);
    expect(wrapper.exists(selector)).toEqual(false);

    const elem = await waitForElement(wrapper, selector);
    expect(elem.props().id).toEqual('test-async-component');
    expect(wrapper.exists(selector)).toEqual(true);
    done();
  });

  it('eventually throws an error for elements that don\'t exist', async (done) => {
    const selector = '#does-not-exist';
    const wrapper = mountWithContexts(<div />);

    let error;
    try {
      await waitForElement(wrapper, selector);
    } catch (err) {
      error = err;
    } finally {
      expect(error).toEqual(new Error(`Element not found using ${selector}`));
      done();
    }
  });
});
