## AWX E2E

```shell
# setup
(container)$ awx-manage createsuperuser --noinput --username=awx-e2e --email=abc@123.com
(container)$ awx-manage update_password --username=awx-e2e --password=password

# run with single worker using a live browser
(host)$ AWX_E2E_URL='https://localhost:8043' npm --prefix awx/ui run e2e -- --env=debug
```