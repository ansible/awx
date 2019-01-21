Credential Plugins
================================
### Development
```shell
# The vault server will be available at localhost:8200.
# From within the awx container, the vault server is reachable at hashivault:8200.
# See docker-hashivault-override.yml for the development root token.
make docker-compose-hashivault
```
