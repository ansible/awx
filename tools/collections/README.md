### Inventory Updates Cross-Development with Collections

Inventory updates in production use vendored collections baked into the image,
which are downloaded from Ansible Galaxy in the build steps.

This gives instructions to short-circuit that process for a faster development process.

Running this script will do a `git clone` for all the relevant collections
into the folder `awx/plugins/collections`.

```
source tools/collections/clone_vendor.sh
```

After this is completed, you must change the path where the server looks
for the vendored inventory collections.
Add this line to your local settings:

```
INVENTORY_COLLECTIONS_ROOT = '/awx_devel/awx/plugins/collections'
```

Then when you run an inventory update of a particular type, it should
use the cloned collection.
This allows you to cd into a particular collection, add remotes,
change branches, etc.

#### Extra Build Steps

This will not work correctly in all circumstances.
Some collections make changes at build-time.

In particular, the foreman inventory plugin needs the NAME attribute changed to
the fully-qualified collection name, and will fail if this is not done.
