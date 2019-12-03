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


## CI Container

To run:

```shell
cd awx/awx/ui_next
docker build -t awx-ui-next .
docker run --name tools_ui_next_1 --network tools_default --link 'tools_awx_1:awx' -e TARGET_HOST=awx -p '3001:3001' --rm -v $(pwd)/src:/ui_next/src awx-ui-next
```

**note:** This is for CI, test systems, zuul, etc. For local development, see [usage](https://github.com/ansible/awx/blob/devel/awx/ui_next/README.md#usage) 
