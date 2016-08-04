from .._errors import StratisCliValueUnimplementedError

def create_pool(dbus_thing, namespace):
    """
    Create a stratis pool.
    """
    if namespace.force:
        raise StratisCliValueUnimplementedError(
           namespace.force,
           "namespace.force"
        )

    if namespace.redundancy != 'none':
        raise StratisCliValueUnimplementedError(
           namespace.redundancy,
           "namespace.redundancy"
        )

    (result, rc, message) = dbus_thing.CreatePool(
       namespace.name,
       namespace.device,
       len(namespace.device)
    )

    return (rc, message)

def list_pools(dbus_thing, namespace):
    """
    List all stratis pools.

    :param Interface dbus_thing: the interface to the stratis manager
    """
    (result, rc, message) = dbus_thing.ListPools()
    if rc != 0:
        return (rc, message)

    for item in result:
        print(item)
    return (rc, message)

def destroy_pool(dbus_thing, namespace):
    """
    Destroy a stratis pool.
    """
    if namespace.force:
        raise StratisCliValueUnimplementedError(
           namespace.force,
           "namespace.force"
        )

    (result, rc, message) = dbus_thing.DestroyPool(
       namespace.name
    )

    return (rc, message)
