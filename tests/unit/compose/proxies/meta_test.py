import wrapt

from tiozin.compose import ProxyMeta, tioproxy


class AlphaProxy(wrapt.ObjectProxy):
    pass


class BetaProxy(wrapt.ObjectProxy):
    pass


# ============================================================================
# Testing ProxyMeta - Instantiation
# ============================================================================
def test_meta_should_wrap_instance():
    """ProxyMeta wraps the instance with the registered proxy."""

    # Arrange
    @tioproxy(AlphaProxy)
    class Subject(metaclass=ProxyMeta):
        pass

    # Act
    instance = Subject()

    # Assert
    actual = (
        isinstance(instance, AlphaProxy),
        isinstance(instance, Subject),
        isinstance(instance.__wrapped__, Subject),
    )
    expected = (True, True, True)
    assert actual == expected


def test_meta_should_chain_parent_outermost():
    """ProxyMeta applies parent proxies outermost: Alpha(Beta(instance))."""

    # Arrange
    @tioproxy(AlphaProxy)
    class Parent(metaclass=ProxyMeta):
        pass

    @tioproxy(BetaProxy)
    class Child(Parent):
        pass

    # Act
    instance = Child()

    # Assert
    actual = (
        type(instance),
        type(instance.__wrapped__),
        type(instance.__wrapped__.__wrapped__),
    )
    expected = (AlphaProxy, BetaProxy, Child)
    assert actual == expected


def test_meta_should_deduplicate_proxies():
    """ProxyMeta applies each proxy only once even if repeated in hierarchy."""

    # Arrange
    @tioproxy(AlphaProxy)
    class Parent(metaclass=ProxyMeta):
        pass

    @tioproxy(AlphaProxy)
    class Child(Parent):
        pass

    # Act
    instance = Child()

    # Assert
    actual = (
        type(instance),
        type(instance.__wrapped__),
    )
    expected = (AlphaProxy, Child)
    assert actual == expected


def test_meta_should_preserve_attributes():
    """ProxyMeta preserves the wrapped instance's attributes through the proxy."""

    # Arrange
    @tioproxy(AlphaProxy)
    class Subject(metaclass=ProxyMeta):
        def __init__(self, name):
            self.name = name

    # Act
    instance = Subject("test")

    # Assert
    actual = instance.name
    expected = "test"
    assert actual == expected
