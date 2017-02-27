Run from the root of the repo:

```shell
$ docker-compose -f tools/docker-compose/unit-tests/docker-compose.yml run unit-tests
```

This will start the container, install the dependencies, and run the unit tests.

To rebuild:


```shell
$ docker-compose -f tools/docker-compose/unit-tests/docker-compose.yml build
```

If you just want to pop into a shell and poke around, run:

```shell
$ docker-compose -f tools/docker-compose/unit-tests/docker-compose.yml run unit-tests bash
```

If you run into any weirdness, it's probably a good idea to just give up and `make clean`.
