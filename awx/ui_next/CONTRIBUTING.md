# Ansible AWX UI With PatternFly

Hi there! We're excited to have you as a contributor.

Have questions about this document or anything not covered here? Feel free to reach out to any of the contributors of this repository.

## Table of contents

- [Ansible AWX UI With PatternFly](#ansible-awx-ui-with-patternfly)
  - [Table of contents](#table-of-contents)
  - [Things to know prior to submitting code](#things-to-know-prior-to-submitting-code)
  - [Setting up your development environment](#setting-up-your-development-environment)
    - [Prerequisites](#prerequisites)
      - [Node and npm](#node-and-npm)
      - [Build the User Interface](#build-the-user-interface)
  - [Accessing the AWX web interface](#accessing-the-awx-web-interface)
  - [AWX REST API Interaction](#awx-rest-api-interaction)
  - [Handling API Errors](#handling-api-errors)
  - [Forms](#forms)
  - [Working with React](#working-with-react)
    - [App structure](#app-structure)
    - [Patterns](#patterns)
      - [Bootstrapping the application (root src/ files)](#bootstrapping-the-application-root-src-files)
    - [Naming files](#naming-files)
      - [Naming components that use the context api](#naming-components-that-use-the-context-api)
    - [Class constructors vs Class properties](#class-constructors-vs-class-properties)
    - [Binding](#binding)
    - [Typechecking with PropTypes](#typechecking-with-proptypes)
    - [Custom Hooks](#custom-hooks)
    - [Naming Functions](#naming-functions)
    - [Default State Initialization](#default-state-initialization)
    - [Testing components that use contexts](#testing-components-that-use-contexts)
  - [Internationalization](#internationalization)
    - [Marking strings for translation and replacement in the UI](#marking-strings-for-translation-and-replacement-in-the-ui)
    - [Setting up .po files to give to translation team](#setting-up-po-files-to-give-to-translation-team)
    - [Marking an issue to be translated](#marking-an-issue-to-be-translated)


## Things to know prior to submitting code

- All code submissions are done through pull requests against the `devel` branch.
- If collaborating with someone else on the same branch, please use `--force-with-lease` instead of `--force` when pushing up code. This will prevent you from accidentally overwriting commits pushed by someone else. For more information, see https://git-scm.com/docs/git-push#git-push---force-with-leaseltrefnamegt
- We use a [code formatter](https://prettier.io/). Before adding a new commit or opening a PR, please apply the formatter using `npm run prettier`
- We adopt the following code style guide:
  - functions should adopt camelCase
  - constructors/classes should adopt PascalCase
  - constants to be exported should adopt UPPERCASE
- For strings, we adopt the `sentence capitalization` since it is a [Patternfly style guide](https://www.patternfly.org/v4/design-guidelines/content/grammar-and-terminology#capitalization).

## Setting up your development environment

The UI is built using [ReactJS](https://reactjs.org/docs/getting-started.html) and [Patternfly](https://www.patternfly.org/).

### Prerequisites

#### Node and npm

The AWX UI requires the following:

- Node 10.x LTS
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

## AWX REST API Interaction

This interface is built on top of the AWX REST API. If a component needs to interact with the API then the model that corresponds to that base endpoint will need to be imported from the api module.

Example:

`import { OrganizationsAPI, UsersAPI } from '../../../api';`

All models extend a `Base` class which provides an interface to the standard HTTP methods (GET, POST, PUT etc).  Methods that are specific to that endpoint should be added directly to model's class.

**Mixins** - For related endpoints that apply to several different models a mixin should be used.  Mixins are classes with a number of methods and can be used to avoid adding the same methods to a number of different models.  A good example of this is the Notifications mixin.  This mixin provides generic methods for reading notification templates and toggling them on and off.
Note that mixins can be chained.  See the example below.

Example of a model using multiple mixins:

```javascript
import NotificationsMixin from '../mixins/Notifications.mixin';
import InstanceGroupsMixin from '../mixins/InstanceGroups.mixin';

class Organizations extends InstanceGroupsMixin(NotificationsMixin(Base)) {
  ...
}

export default Organizations;
```

**Testing** - The easiest way to mock the api module in tests is to use jest's [automatic mock](https://jestjs.io/docs/en/es6-class-mocks#automatic-mock).  This syntax will replace the class with a mock constructor and mock out all methods to return undefined by default.  If necessary, you can still override these mocks for specific tests.  See the example below.

Example of mocking a specific method for every test in a suite:

```javascript
import { OrganizationsAPI } from '../../../../src/api';

// Mocks out all available methods.  Comparable to:
// OrganizationsAPI.readAccessList = jest.fn();
// but for every available method
jest.mock('../../../../src/api');

// Return a specific mock value for the readAccessList method
beforeEach(() => {
  OrganizationsAPI.readAccessList.mockReturnValue({ foo: 'bar' });
});

// Reset mocks
afterEach(() => {
  jest.clearAllMocks();
});

...
```

**Test Attributes** -
It should be noted that the `dataCy` prop, as well as its equivalent attribute `data-cy`, are used as flags for any UI test that wants to avoid relying on brittle CSS selectors such as `nth-of-type()`.

## Handling API Errors
API requests can and will fail occasionally so they should include explicit error handling. The three _main_ categories of errors from our perspective are: content loading errors, form submission errors, and other errors. The patterns currently in place for these are described below:

- **content loading errors** - These are any errors that occur when fetching data to initialize a page or populate a list. For these, we conditionally render a _content error component_ in place of the unresolved content.

- **form submission errors** - If an error is encountered when submitting a form, we display the error message on the form. For field-specific validation errors, we display the error message beneath the specific field(s). For general errors, we display the error message at the bottom of the form near the action buttons. An error that happens when requesting data to populate a form is not a form submission error, it is still a content error and is handled as such (see above).

- **other errors** - Most errors will fall into the first two categories, but for miscellaneous actions like toggling notifications, deleting a list item, etc. we display an alert modal to notify the user that their requested action couldn't be performed.

## Forms
Our forms should have a known, consistent, and fully-resolved starting state before it is possible for a user, keyboard-mouse, screen reader, or automated test to interact with them. If multiple network calls are needed to populate a form, resolve them all before displaying the form or showing a content error. When multiple requests are needed to create or update the resources represented by a form, resolve them all before transitioning the ui to a success or failure state.

## Working with React

### App structure

All source code lives in the `/src` directory and all tests are colocated with the components that they test.

Inside these folders, the internal structure is:
- **/api** - All classes used to interact with API's are found here.  See [AWX REST API Interaction](#awx-rest-api-interaction) for more information.
- **/components** - All generic components that are meant to be used in multiple contexts throughout awx.  Things like buttons, tabs go here.
- **/contexts** - Components which utilize react's context api.
- **/locales** - [Internationalization](#internationalization) config and source files.
- **/screens** - Based on the various routes of awx.
  - **/shared** - Components that are meant to be used specifically by a particular route, but might be sharable across pages of that route. For example, a form component which is used on both add and edit screens.
- **/util** - Stateless helper functions that aren't tied to react.

### Patterns
- A **screen** shouldn't import from another screen. If a component _needs_ to be shared between two or more screens, it is a generic and should be moved to `src/components`.

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

**Component naming and conventions** - In order to provide a consistent interface with react-router and [lingui](https://lingui.js.org/), as well as make their usage easier and less verbose, context components follow these conventions:
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

### Custom Hooks

There are currently a few custom hooks:

1. [useRequest](https://github.com/ansible/awx/blob/devel/awx/ui_next/src/util/useRequest.js#L21) encapsulates main actions related to requests.
2. [useDismissableError](https://github.com/ansible/awx/blob/devel/awx/ui_next/src/util/useRequest.js#L71) provides controls for "dismissing" an error message.
3. [useDeleteItems](https://github.com/ansible/awx/blob/devel/awx/ui_next/src/util/useRequest.js#L98) handles deletion of items from a paginated item list.
4. [useSelected](https://github.com/ansible/awx/blob/devel/awx/ui_next/src/util/useSelected.jsx#L14) provides a way to read and update a selected list.

### Naming Functions
Here are the guidelines for how to name functions.

| Naming Convention | Description                                                                       |
| ----------------- | --------------------------------------------------------------------------------- |
| `handle<x>`       | Use for methods that process events                                               |
| `on<x>`           | Use for component prop names                                                      |
| `toggle<x>`       | Use for methods that flip one value to the opposite value                         |
| `show<x>`         | Use for methods that always set a value to show or add an element                 |
| `hide<x>`         | Use for methods that always set a value to hide or remove an element              |
| `create<x>`       | Use for methods that make API `POST` requests                                     |
| `read<x>`         | Use for methods that make API `GET` requests                                      |
| `update<x>`       | Use for methods that make API `PATCH` requests                                    |
| `destroy<x>`      | Use for methods that make API `DESTROY` requests                                  |
| `replace<x>`      | Use for methods that make API `PUT` requests                                      |
| `disassociate<x>` | Use for methods that pass `{ disassociate: true }` as a data param to an endpoint |
| `associate<x>`    | Use for methods that pass a resource id as a data param to an endpoint            |
| `can<x>`          | Use for props dealing with RBAC to denote whether a user has access to something  |

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

### Testing components that use contexts

We have several React contexts that wrap much of the app, including those from react-router, lingui, and some of our own. When testing a component that depends on one or more of these, you can use the `mountWithContexts()` helper function found in `testUtils/enzymeHelpers.jsx`. This can be used just like Enzyme's `mount()` function, except it will wrap the component tree with the necessary context providers and basic stub data.

If you want to stub the value of a context, or assert actions taken on it, you can customize a contexts value by passing a second parameter to `mountWithContexts`. For example, this provides a custom value for the `Config` context:

```javascript
const config = {
  custom_virtualenvs: ['foo', 'bar'],
};
mountWithContexts(<OrganizationForm />, {
  context: { config },
});
```

Now that these custom virtual environments are available in this `OrganizationForm` test we can assert that the component that displays
them is rendering properly.

The object containing context values looks for five known contexts, identified by the keys `linguiPublisher`, `router`, `config`, `network`, and `dialog` — the latter three each referring to the contexts defined in `src/contexts`. You can pass `false` for any of these values, and the corresponding context will be omitted from your test. For example, this will mount your component without the dialog context:

```javascript
mountWithContexts(<Organization />< {
  context: {
    dialog: false,
  }
});
```

## Internationalization

Internationalization leans on the [lingui](https://github.com/lingui/js-lingui) project.  [Official documentation here](https://lingui.js.org/).  We use this library to mark our strings for translation.  If you want to see this in action you'll need to take the following steps:

### Marking strings for translation and replacement in the UI

The lingui library provides various React helpers for dealing with both marking strings for translation, and replacing strings that have been translated.  For consistency and ease of use, we have consolidated on one pattern for the codebase.  To set strings to be translated in the UI:

- import the withI18n function and wrap the export of your component in it (i.e. `export default withI18n()(Foo)`)
- doing the above gives you access to the i18n object on props.  Make sure to put it in the scope of the function that contains strings needed to be translated (i.e. `const { i18n } = this.props;`)
- import the t template tag function from the @lingui/macro package.
- wrap your string using the following format: ```i18n._(t`String to be translated`)```

**Note:** Variables that are put inside the t-marked template tag will not be translated.  If you have a variable string with text that needs translating, you must wrap it in ```i18n._(t``)``` where it is defined.

**Note:** We try to avoid the `I18n` consumer, `i18nMark` function, or `<Trans>` component lingui gives us access to in this repo.  i18nMark does not actually replace the string in the UI (leading to the potential for untranslated bugs), and the other helpers are redundant.  Settling on a consistent, single pattern helps us ease the mental overhead of the need to understand the ins and outs of the lingui API.

You can learn more about the ways lingui and its React helpers at [this link](https://lingui.js.org/tutorials/react-patterns.html).

### Setting up .po files to give to translation team

1) `npm run add-locale` to add the language that you want to translate to (we should only have to do this once and the commit to repo afaik).  Example: `npm run add-locale en es fr`  # Add English, Spanish and French locale
2) `npm run extract-strings` to create .po files for each language specified.  The .po files will be placed in src/locales.
3) Open up the .po file for the language you want to test and add some translations.  In production we would pass this .po file off to the translation team.
4) Once you've edited your .po file (or we've gotten a .po file back from the translation team) run `npm run compile-strings`.  This command takes the .po files and turns them into a minified JSON object and can be seen in the `messages.js` file in each locale directory.  These files get loaded at the App root level (see: App.jsx).
5) Change the language in your browser and reload the page.  You should see your specified translations in place of English strings.

### Marking an issue to be translated

1) Issues marked with `component:I10n` should not be closed after the issue was fixed.
2) Remove the label `state:needs_devel`.
3) Add the label `state:pending_translations`. At this point, the translations will be batch translated by a maintainer, creating relevant entries in the PO files. Then after those translations have been merged, the issue can be closed.
