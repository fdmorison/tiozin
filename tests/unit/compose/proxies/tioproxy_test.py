import pytest
import wrapt

from tiozin.compose import ProxyMeta, tioproxy
from tiozin.exceptions import ProxyContractViolationError


class AlphaProxy(wrapt.ObjectProxy):
    pass


class BetaProxy(wrapt.ObjectProxy):
    pass


# ============================================================================
# Testing @tioproxy - Registration
# ============================================================================
def test_tioproxy_should_register_proxy():
    """@tioproxy(Proxy) sets __tioproxy__ = [Proxy] on the class."""

    # Act
    @tioproxy(AlphaProxy)
    class Subject(metaclass=ProxyMeta):
        pass

    # Assert
    actual = Subject.__tioproxy__
    expected = [AlphaProxy]
    assert actual == expected


def test_tioproxy_should_stack_proxies():
    """Stacking @tioproxy accumulates proxies in top-to-bottom declaration order."""

    # Act
    @tioproxy(AlphaProxy)
    @tioproxy(BetaProxy)
    class Subject(metaclass=ProxyMeta):
        pass

    # Assert
    actual = Subject.__tioproxy__
    expected = [BetaProxy, AlphaProxy]
    assert actual == expected


def test_tioproxy_should_reject_invalid_class():
    """@tioproxy raises if the proxy does not inherit from ObjectProxy."""

    # Arrange
    class NotAProxy:
        pass

    # Act & Assert
    with pytest.raises(ProxyContractViolationError):

        @tioproxy(NotAProxy)
        class Subject(metaclass=ProxyMeta):
            pass


# ============================================================================
# Testing @tioproxy - Inheritance
# ============================================================================
def test_tioproxy_should_inherit_parent_proxies():
    """Child's __tioproxy__ contains parent proxies followed by its own."""

    # Arrange
    @tioproxy(AlphaProxy)
    class Parent(metaclass=ProxyMeta):
        pass

    # Act
    @tioproxy(BetaProxy)
    class Child(Parent):
        pass

    # Assert
    actual = Child.__tioproxy__
    expected = [AlphaProxy, BetaProxy]
    assert actual == expected


def test_tioproxy_should_not_mutate_parent():
    """Decorating a child does not alter the parent's __tioproxy__."""

    # Arrange
    @tioproxy(AlphaProxy)
    class Parent(metaclass=ProxyMeta):
        pass

    # Act
    @tioproxy(BetaProxy)
    class Child(Parent):
        pass

    # Assert
    actual = Parent.__tioproxy__
    expected = [AlphaProxy]
    assert actual == expected


def test_tioproxy_should_keep_duplicate_from_parent():
    """When child repeats a parent proxy, __tioproxy__ keeps both entries."""

    # Arrange
    @tioproxy(AlphaProxy)
    class Parent(metaclass=ProxyMeta):
        pass

    # Act
    @tioproxy(AlphaProxy)
    class Child(Parent):
        pass

    # Assert
    actual = Child.__tioproxy__
    expected = [AlphaProxy, AlphaProxy]
    assert actual == expected
