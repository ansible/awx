## AWX E2E
```shell
# setup
docker exec -i tools_awx_1 sh <<-EOSH
  awx-manage createsuperuser --noinput --username=awx-e2e --email=null@ansible.com
  awx-manage update_password --username=awx-e2e --password=password
  make --directory=/awx_devel DATA_GEN_PRESET=e2e bulk_data
EOSH

# run all of the tests with a live browser
npm --prefix awx/ui run e2e

# run a subset of the tests
npm --prefix awx/ui run e2e -- --filter="test-credentials*"

# setup a local webdriver cluster for test development
docker-compose \
  -f awx/ui/test/e2e/cluster/docker-compose.yml \
  -f awx/ui/test/e2e/cluster/docker-compose.devel-override.yml \
  up --scale chrome=2 hub chrome

# run headlessly on the cluster
AWX_E2E_LAUNCH_URL='https://awx:8043' npm --prefix awx/ui run e2e -- --env=cluster

# run with multiple workers
AWX_E2E_LAUNCH_URL='https://awx:8043' AWX_E2E_CLUSTER_WORKERS=2 \
  npm --prefix awx/ui run e2e -- --env=cluster --filter="test-*"
```

**Note:**
- Unless overridden in [settings](settings.js), tests will run against `localhost:8043`.
- Use `npm --prefix awx/ui run e2e -- --help` to see additional usage information for the test runner.
