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
  * [App structure](#app-structure)
  * [Naming files](#naming-files)
  * [Class constructors vs Class properties](#class-constructors-vs-class-properties)
  * [Binding](#binding)
  * [Typechecking with PropTypes](#typechecking-with-proptypes)
  * [Naming Functions](#naming-functions)
  * [Default State Initialization](#default-state-initialization)


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

### App structure

All source code lives in the `/src` directory and all tests live in the `/__tests__` directory (mimicing the internal structure of `/src`).

Inside these folders, the internal structure is:
- **/components** - All generic components that are meant to be used in multiple contexts throughout awx.  Things like buttons, tabs go here.
- **/contexts** - Components which utilize react's context api.
- **/pages** - Based on the various routes of awx.
  - **/components** - Components that are meant to be used specifically by a particular route, but might be sharable across pages of that route. For example, a form component which is used on both add and edit screens.
  - **/screens** - Individual pages of the route, such as add, edit, list, related lists, etc.
- **/util** - Stateless helper functions that aren't tied to react.

#### Bootstrapping the application (root src/ files)

In the root of `/src`, there are a few files which are used to initialize the react app.  These are

- **index.jsx**
  - Connects react app to root dom node.
  - Sets up root route structure, navigation grouping and login modal
  - Calls base context providers
  - Imports .scss styles.
- **app.jsx**
  - Sets standard page layout, about modal, and root dialog modal.
- **RootProvider.jsx**
  - Sets up all context providers.
  - Initializes i18n and router

### Naming files

Ideally, files should be named the same as the component they export, and tests with `.test` appended.  In other words, `<FooBar>` would be defined in `FooBar.jsx`, and its tests would be defined in `FooBar.test.jsx`.

#### Naming components that use the context api

**File naming** - Since contexts export both consumer and provider (and potentially in withContext function form), the file can be simplified to be named after the consumer export.  In other words, the file containing the `Network` context components would be named `Network.jsx`.

**Component naming and conventions** - In order to provide a consistent interface with react-router and lingui, as well as make their usage easier and less verbose, context components follow these conventions:
- Providers are wrapped in a component in the `FooProvider` format.
  - The value prop of the provider should be pulled from state.  This is recommended by the react docs, [here](https://reactjs.org/docs/context.html#caveats).
  - The provider should also be able to accept its value by prop for testing.
  - Any sort of code related to grabbing data to put on the context should be done in this component.
- Consumers are wrapped in a component in the `Foo` format.
- If it makes sense, consumers can be exported as a function in the `withFoo()` format.  If a component is wrapped in this function, its context values are available on the component as props.

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

### Naming Functions
Here are the guidelines for how to name functions.

| Naming Convention   |      Description   |
|----------|-------------|
|`handle<x>`| Use for methods that process events |
|`on<x>`| Use for component prop names |
|`toggle<x>`| Use for methods that flip one value to the opposite value |
|`show<x>`| Use for methods that always set a value to show or add an element |
|`hide<x>`| Use for methods that always set a value to hide or remove an element |
|`create<x>`| Use for methods that make API `POST` requests |
|`read<x>`| Use for methods that make API `GET` requests |
|`update<x>`| Use for methods that make API `PATCH` requests |
|`destroy<x>`| Use for methods that make API `DESTROY` requests |
|`replace<x>`| Use for methods that make API `PUT` requests |
|`disassociate<x>`| Use for methods that pass `{ disassociate: true }` as a data param to an endpoint |
|`associate<x>`| Use for methods that pass a resource id as a data param to an endpoint |

### Default State Initialization
When declaring empty initial states, prefer the following instead of leaving them undefined:

```javascript
this.state = {
  somethingA: null,
  somethingB: [],
  somethingC: 0,
  somethingD: {},
  somethingE: '',
}
```