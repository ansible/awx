## AWX E2E
```shell
# setup
docker exec -i tools_awx_1 sh <<-EOSH
  awx-manage createsuperuser --noinput --username=awx-e2e --email=null@ansible.com
  awx-manage update_password --username=awx-e2e --password=password
  make --directory=/awx_devel DATA_GEN_PRESET=e2e bulk_data
EOSH

# run with with a live browser
npm --prefix awx/ui run e2e -- --env=debug

# setup a local webdriver cluster for test development
docker-compose \
  -f awx/ui/client/test/e2e/cluster/docker-compose.yml \
  -f awx/ui/client/test/e2e/cluster/devel-override.yml \
  up --scale chrome=2 --scale firefox=0

# run headlessly with multiple workers on the cluster
AWX_E2E_LAUNCH_URL='https://awx:8043' AWX_E2E_WORKERS=2 npm --prefix awx/ui run e2e
```

**Note:** Unless overridden in [settings](settings.js), tests will run against `localhost:8043`.
