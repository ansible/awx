# Building the AWX Image

## Build & Push Image

To build a custom awx image to use with the awx-operator, use the `build_image` role:

```
$ ansible-playbook tools/ansible/build.yml -v -e awx_image=registry.example.com/awx -e awx_version=test
```

This will build an AWX image and tag it.  You can then push that image to your container registry:


```
$ docker push registry.example.com/awx:test
```


## Using this image with the awx-operator

In the spec section of the `my-awx.yml` file described in the [install docs](./../INSTALL.md#deploy-awx),
specify the new custom image.  

```
spec:
  tower_image: registry.example.com/awx
  tower_image_version: test
```
