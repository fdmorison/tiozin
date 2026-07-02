from tiozin.utils.decorators import ensure_setup

# ============================================================================
# Testing ensure_setup()
# ============================================================================


def test_ensure_setup_should_run_setup_before_first_public_method_call():
    # Arrange
    @ensure_setup
    class Component:
        def __init__(self):
            self.events = []

        def setup(self):
            self.events.append("setup")

        def work(self):
            self.events.append("work")

    component = Component()

    # Act
    component.work()

    # Assert
    actual = component.events
    expected = ["setup", "work"]
    assert actual == expected


def test_ensure_setup_should_run_setup_only_once_across_multiple_method_calls():
    # Arrange
    @ensure_setup
    class Component:
        def __init__(self):
            self.setup_calls = 0

        def setup(self):
            self.setup_calls += 1

        def work(self):
            pass

    component = Component()

    # Act
    component.work()
    component.work()
    component.work()

    # Assert
    actual = component.setup_calls
    expected = 1
    assert actual == expected


def test_ensure_setup_should_run_setup_before_first_property_read():
    # Arrange
    @ensure_setup
    class Component:
        def __init__(self):
            self.events = []

        def setup(self):
            self.events.append("setup")

        @property
        def value(self):
            self.events.append("read")
            return 42

    component = Component()

    # Act
    _ = component.value

    # Assert
    actual = component.events
    expected = ["setup", "read"]
    assert actual == expected


def test_ensure_setup_should_run_setup_before_first_property_write():
    # Arrange
    @ensure_setup
    class Component:
        def __init__(self):
            self.events = []
            self._value = None

        def setup(self):
            self.events.append("setup")

        @property
        def value(self):
            return self._value

        @value.setter
        def value(self, new_value):
            self.events.append("write")
            self._value = new_value

    component = Component()

    # Act
    component.value = 99

    # Assert
    actual = component.events
    expected = ["setup", "write"]
    assert actual == expected


def test_ensure_setup_should_not_wrap_setup_and_teardown():
    # Arrange
    @ensure_setup
    class Component:
        def __init__(self):
            self.events = []

        def setup(self):
            self.events.append("setup")

        def teardown(self):
            self.events.append("teardown")

    component = Component()

    # Act
    component.setup()
    component.teardown()

    # Assert
    actual = component.events
    expected = ["setup", "teardown"]
    assert actual == expected


def test_ensure_setup_should_not_run_setup_when_calling_private_method():
    # Arrange
    @ensure_setup
    class Component:
        def __init__(self):
            self.events = []

        def setup(self):
            self.events.append("setup")

        def _helper(self):
            self.events.append("helper")

    component = Component()

    # Act
    component._helper()

    # Assert
    actual = component.events
    expected = ["helper"]
    assert actual == expected


def test_ensure_setup_should_not_recurse_when_setup_uses_public_members():
    # Arrange
    @ensure_setup
    class Component:
        def __init__(self):
            self.setup_calls = 0

        def setup(self):
            self.setup_calls += 1
            self.work()

        def work(self):
            pass

    component = Component()

    # Act
    component.work()

    # Assert
    actual = component.setup_calls
    expected = 1
    assert actual == expected


def test_ensure_setup_should_retry_setup_when_previous_setup_raised():
    # Arrange
    @ensure_setup
    class Component:
        def __init__(self):
            self.setup_calls = 0

        def setup(self):
            self.setup_calls += 1
            if self.setup_calls == 1:
                raise RuntimeError("boom")

        def work(self):
            pass

    component = Component()
    try:
        component.work()
    except RuntimeError:
        pass

    # Act
    component.work()

    # Assert
    actual = component.setup_calls
    expected = 2
    assert actual == expected


def test_ensure_setup_should_reset_ensuring_flag_when_setup_raises():
    # Arrange
    @ensure_setup
    class Component:
        def setup(self):
            raise RuntimeError("boom")

        def work(self):
            pass

    component = Component()
    try:
        component.work()
    except RuntimeError:
        pass

    # Act
    actual = component._ensuring_setup

    # Assert
    expected = False
    assert actual == expected
