import pytest
import wrapt

from tiozin.compose import TioProxyMeta, tioproxy
from tiozin.exceptions import DuplicateProxyDecoratorError, ProxyContractViolationError


class AlphaProxy(wrapt.ObjectProxy):
    pass


class BetaProxy(wrapt.ObjectProxy):
    pass


# ============================================================================
# Testing @tioproxy - Registration
# ============================================================================
def test_tioproxy_should_register_proxy():
    """@tioproxy(Proxy) registers the proxy in the class's proxy list."""

    # Act
    @tioproxy(AlphaProxy)
    class Subject(metaclass=TioProxyMeta):
        pass

    # Assert
    actual = Subject.tioproxy
    expected = [AlphaProxy]
    assert actual == expected


def test_tioproxy_should_accept_multiple_proxies():
    """@tioproxy(A, B) registers proxies in the given parameter order."""

    # Act
    @tioproxy(AlphaProxy, BetaProxy)
    class Subject(metaclass=TioProxyMeta):
        pass

    # Assert
    actual = Subject.tioproxy
    expected = [AlphaProxy, BetaProxy]
    assert actual == expected


def test_tioproxy_should_reject_invalid_class():
    """@tioproxy raises if the proxy does not inherit from ObjectProxy."""

    # Arrange
    class NotAProxy:
        pass

    # Act & Assert
    with pytest.raises(ProxyContractViolationError):

        @tioproxy(NotAProxy)
        class Subject(metaclass=TioProxyMeta):
            pass


def test_tioproxy_should_reject_duplicate_decorator():
    """@tioproxy raises if applied more than once to the same class."""

    # Act & Assert
    with pytest.raises(DuplicateProxyDecoratorError):

        @tioproxy(BetaProxy)
        @tioproxy(AlphaProxy)
        class Subject(metaclass=TioProxyMeta):
            pass


# ============================================================================
# Testing @tioproxy - Inheritance
# ============================================================================
def test_tioproxy_should_inherit_parent_proxies():
    """Child's proxy list contains parent proxies followed by its own."""

    # Arrange
    @tioproxy(AlphaProxy)
    class Parent(metaclass=TioProxyMeta):
        pass

    # Act
    @tioproxy(BetaProxy)
    class Child(Parent):
        pass

    # Assert
    actual = Child.tioproxy
    expected = [AlphaProxy, BetaProxy]
    assert actual == expected


def test_tioproxy_should_not_mutate_parent():
    """Decorating a child does not alter the parent's proxy list."""

    # Arrange
    @tioproxy(AlphaProxy)
    class Parent(metaclass=TioProxyMeta):
        pass

    # Act
    @tioproxy(BetaProxy)
    class Child(Parent):
        pass

    # Assert
    actual = Parent.tioproxy
    expected = [AlphaProxy]
    assert actual == expected


def test_tioproxy_should_deduplicate_from_parent():
    """When child repeats a parent proxy, the proxy list deduplicates it."""

    # Arrange
    @tioproxy(AlphaProxy)
    class Parent(metaclass=TioProxyMeta):
        pass

    # Act
    @tioproxy(AlphaProxy)
    class Child(Parent):
        pass

    # Assert
    actual = Child.tioproxy
    expected = [AlphaProxy]
    assert actual == expected


# ============================================================================
# Testing TioProxyMeta - Instantiation
# ============================================================================
def test_meta_should_wrap_instance():
    """TioProxyMeta wraps the instance with the registered proxy."""

    # Arrange
    @tioproxy(AlphaProxy)
    class Subject(metaclass=TioProxyMeta):
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
    """TioProxyMeta applies parent proxies outermost: Alpha(Beta(instance))."""

    # Arrange
    @tioproxy(AlphaProxy)
    class Parent(metaclass=TioProxyMeta):
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


def test_meta_should_preserve_attributes():
    """TioProxyMeta preserves the wrapped instance's attributes through the proxy."""

    # Arrange
    @tioproxy(AlphaProxy)
    class Subject(metaclass=TioProxyMeta):
        def __init__(self, name):
            self.name = name

    # Act
    instance = Subject("test")

    # Assert
    actual = instance.name
    expected = "test"
    assert actual == expected
