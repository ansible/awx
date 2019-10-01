# AWX-PF

## Requirements
- node 10.x LTS, npm 6.x LTS, make, git

## Usage

* `git clone git@github.com:ansible/awx.git`
* cd awx/ui_next
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
* `npm test -- src/screens/Login/Login.test.jsx`

**note:** Once the test watcher is up and running you can hit `a` to run all the tests
