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

    return

def list_pools(dbus_thing, namespace):
    """
    List all stratis pools.

    :param Interface dbus_thing: the interface to the stratis manager
    """
    (result, rc, message) = dbus_thing.ListPools()
    if rc != 0:
        print(message)
    else:
        for item in result:
            print(item)
    return

def destroy_pool(dbus_thing, namespace):
    """
    Destroy a stratis pool.
    """
    if namespace.force:
        raise StratisCliValueUnimplementedError(
           namespace.force,
           "namespace.force"
        )

    return
