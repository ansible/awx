## AWX E2E

```shell
# setup
(container)$ awx-manage createsuperuser --noinput --username=awx-e2e --email=abc@123.com
(container)$ awx-manage update_password --username=awx-e2e --password=password

# run with single worker using a live browser
(host)$ AWX_E2E_URL='https://localhost:8043' npm --prefix awx/ui run e2e -- --env=debug

# run with multiple workers using local webdriver cluster
(host)$ docker-compose \
  -f awx/ui/client/test/e2e/cluster/docker-compose.yml \
  -f awx/ui/client/test/e2e/cluster/devel-override.yml \
  up --scale chrome=2 --scale firefox=0

(host)$ npm --prefix awx/ui run e2e
```
