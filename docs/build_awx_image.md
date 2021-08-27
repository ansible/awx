# Building the AWX Image

## Build & Push Image

To build a custom awx image to use with the awx-operator, use the `build_image` role:

```
$ ansible-playbook tools/ansible/build.yml \
    -e registry=registry.example.com \
    -e awx_image=ansible/awx \
    -e awx_version=test -v
```

> Note: The development image (`make docker-compose-build`) will not work with the awx-operator, the UI is not built in that image, among other things (see Dockerfile.j2 for more info).

This will build an AWX image and tag it.  You can then push that image to your container registry:


```
$ docker push registry.example.com/awx:test
```


## Using this image with the awx-operator

In the [Advanced Configuration](https://github.com/ansible/awx-operator/blob/devel/README.md#advanced-configuration)
section of the [README.md](https://github.com/ansible/awx-operator/blob/devel/README.md) of the AWX Operator repository,
update the `spec` section of the `awx-demo.yml` file as follows:

```
spec:
  image: registry.example.com/awx
  image_version: test
```
