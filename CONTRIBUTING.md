# Ansible AWX/Tower V2

Hi there! We're excited to have you as a contributor.

Have questions about this document or anything not covered here? Feel free to reach out to any of the contributors of this repository found here: https://github.com/ansible/awx-pf/graphs/contributors

## Table of contents

* [Things to know prior to submitting code](#things-to-know-prior-to-submitting-code)
* [Setting up your development environment](#setting-up-your-development-environment)
  * [Prerequisites](#prerequisites)
    * [Node and npm](#node-and-npm)
* [Build the user interface](#build-the-user-interface)
* [Accessing the AWX web interface](#accessing-the-awx-web-interface)
* [Working with React](#working-with-react)
  * [Class constructors vs Class properties](#class-constructors-vs-class-properties)
  * [Binding](#binding)
  * [Typechecking with PropTypes](#typechecking-with-proptypes)
* [Testing](#testing)
  * [Jest](#jest)
  * [Enzyme](#enzyme)

## Things to know prior to submitting code

- All code submissions are done through pull requests against the `master` branch.
- If collaborating with someone else on the same branch, please use `--force-with-lease` instead of `--force` when pushing up code. This will prevent you from accidentally overwriting commits pushed by someone else. For more information, see https://git-scm.com/docs/git-push#git-push---force-with-leaseltrefnamegt

## Setting up your development environment

The UI is built using [ReactJS](https://reactjs.org/docs/getting-started.html) and [Patternfly](https://www.patternfly.org/).

### Prerequisites

#### Node and npm

The AWX UI requires the following:

- Node 8.x LTS
- NPM 6.x LTS

Run the following to install all the dependencies:
```bash
(host) $ npm run install
```

#### Build the User Interface

Run the following to build the AWX UI:

```bash
(host) $ npm run start
```

## Accessing the AWX web interface

You can now log into the AWX web interface at [https://127.0.0.1:3001](https://127.0.0.1:3001).

## Working with React
### Class constructors vs Class properties
It is good practice to use constructor-bound instance methods rather than methods as class properties. Methods as arrow functions provide lexical scope and are bound to the Component class instance instead of the class itself. This makes it so we cannot easily test a Component's methods without invoking an instance of the Component and calling the method directly within our tests.

BAD:
  ```javascript
    class MyComponent extends React.Component {
      constructor(props) {
        super(props);
      }

      myEventHandler = () => {
        // do a thing
      }
    }
  ```
GOOD:
  ```javascript
    class MyComponent extends React.Component {
      constructor(props) {
        super(props);
        this.myEventHandler = this.myEventHandler.bind(this);
      }

      myEventHandler() {
        // do a thing
      }
    }
  ```

### Binding
It is good practice to bind our class methods within our class constructor method for the following reasons:
  1. Avoid defining the method every time `render()` is called.
  2. [Performance advantages](https://stackoverflow.com/a/44844916).
  3. Ease of [testing](https://github.com/airbnb/enzyme/issues/365).

### Typechecking with PropTypes
Shared components should have their prop values typechecked. This will help catch bugs when components get refactored/renamed.
```javascript
About.propTypes = {
  ansible_version: PropTypes.string,
  isOpen: PropTypes.bool,
  onClose: PropTypes.func.isRequired,
  version: PropTypes.string,
};

About.defaultProps = {
  ansible_version: null,
  isOpen: false,
  version: null,
};
```



## Testing
All code, new or otherwise, should have at least 80% test coverage.
### Jest
We use (Jest)[https://jestjs.io/] for our JS testing framework.
Like many other JS test frameworks (Karma, Mocha, etc), Jest includes their own `spyOn` method as a way for us to test our class methods.
```javascript
  const spy = jest.spyOn(MyButton.prototype, 'onSubmit');
```

Jest also allows us to mock the data we expect from an external dependency, such as an API.
```javascript
  axios.get.mockImplementation((endpoint) => {
    if (endpoint === '/api/v2/config') {
      return new Promise((resolve, reject) => {
        resolve({ data: { foo: 'bar' });
      });
    }
    else {
      return 'get results';
    }
  });
```

### Enzyme
We use (Enzyme)[https://airbnb.io/enzyme/] to test our React Components.
### Mounting Components wrapped with withRouter
If you are testing a Component wrapped in React Router's `withRouter` class, you can mount the component by wrapping it with the `<MemoryRouter>` component.
```javascript
  test('initially renders succesfully', () => {
    mount(
       <MemoryRouter>
        <OrganizationAdd
          match={{ path: '/organizations/add', url: '/organizations/add' }}
          location={{ search: '', pathname: '/organizations/add' }}
        />
      </MemoryRouter>
     );
   });
```
You can test the wrapped Component's methods like so:
```javascript
  const spy = jest.spyOn(OrganizationAdd.WrappedComponent.prototype, 'onCancel');
```
