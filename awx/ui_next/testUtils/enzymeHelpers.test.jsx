import React, { Component } from 'react';
import { createMemoryHistory } from 'history';
import { Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { mountWithContexts, waitForElement } from './enzymeHelpers';
import { Config } from '../src/contexts/Config';

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
      const Parent = () => <Child />;
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
          history: createMemoryHistory({}),
          route: {
            location: {},
            match: {},
          },
        },
      };
      const wrapper = mountWithContexts(
        <div>
          <Link to="/">home</Link>
        </div>,
        { context }
      );

      const link = wrapper.find('Link');
      expect(link).toHaveLength(1);
      link.simulate('click', { button: 0 });
      wrapper.update();

      expect(context.router.history.location.pathname).toEqual('/');
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
      const wrapper = mountWithContexts(<Foo />, { context: { config } });
      expect(wrapper.find('Foo')).toMatchSnapshot();
    });
  });
});

/**
 * This is a fixture for testing async components. It renders a div
 * after a short amount of time.
 */
class TestAsyncComponent extends Component {
  constructor(props) {
    super(props);
    this.state = { displayElement: false };
  }

  componentDidMount() {
    setTimeout(() => this.setState({ displayElement: true }), 500);
  }

  render() {
    const { displayElement } = this.state;
    if (displayElement) {
      return <div id="test-async-component" />;
    }
    return null;
  }
}

describe('waitForElement', () => {
  it('waits for the element and returns it', async done => {
    const selector = '#test-async-component';
    const wrapper = mountWithContexts(<TestAsyncComponent />);
    expect(wrapper.exists(selector)).toEqual(false);

    const elem = await waitForElement(wrapper, selector);
    expect(elem.props().id).toEqual('test-async-component');
    expect(wrapper.exists(selector)).toEqual(true);
    done();
  });

  it("eventually throws an error for elements that don't exist", async done => {
    const wrapper = mountWithContexts(<div />);

    let error;
    try {
      await waitForElement(wrapper, '#does-not-exist');
    } catch (err) {
      error = err;
    } finally {
      expect(error.message).toContain('Expected condition for <#does-not-exist> not met');
      expect(error.message).toContain('el.length === 1');
      done();
    }
  });
});
