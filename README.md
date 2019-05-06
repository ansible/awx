# AWX-PF

## Requirements
- node 8.x LTS, npm 5.x LTS, make, git

## Usage

* `git clone git@github.com:ansible/awx-pf.git`
* cd awx-pf
* npm install
* npm start
* visit `https://127.0.0.1:3001/`

**note:** These instructions assume you have the [awx](https://github.com/ansible/awx/blob/devel/CONTRIBUTING.md#running-the-environment) development api server up and running at `localhost:8043`. You can use a different backend server with the `TAGET_HOST` and `TARGET_PORT` environment variables when starting the development server:

```shell
# use a non-default host and port when starting the development server
TARGET_HOST='ec2-awx.amazonaws.com' TARGET_PORT='443' npm run start
```

## Unit Tests

To run the unit tests on files that you've changed:
* `npm test`

To run a single test (in this case the login page test):
* `npm test -- __tests__/pages/Login.jsx`

**note:** Once the test watcher is up and running you can hit `a` to run all the tests

## Internationalization

Internationalization leans on the [lingui](https://github.com/lingui/js-lingui) project.  [Official documentation here](https://lingui.js.org/).  We use this libary to mark our strings for translation.  For common React use cases see [this link](https://lingui.js.org/tutorials/react-patterns.html).  If you want to see this in action you'll need to take the following steps:

1) `npm run add-locale` to add the language that you want to translate to (we should only have to do this once and the commit to repo afaik).  Example: `npm run add-locale en es fr`  # Add English, Spanish and French locale
2) `npm run extract-strings` to create .po files for each language specified.  The .po files will be placed in src/locales but this is configurable.
3) Open up the .po file for the language you want to test and add some translations.  In production we would pass this .po file off to the translation team.
4) Once you've edited your .po file (or we've gotten a .po file back from the translation team) run `npm run compile-strings`.  This command takes the .po files and turns them into a minified JSON object and can be seen in the `messages.js` file in each locale directory.  These files get loaded at the App root level (see: App.jsx).
5) Change the language in your browser and reload the page.  You should see your specified translations in place of English strings.
