from importlib.metadata import EntryPoint
from unittest.mock import Mock

import pytest

from tiozin.compose.policies import (
    FamilyNamePolicy,
    InputNamingPolicy,
    OutputNamingPolicy,
    PolicyDecision,
    PolicyResult,
    RegistryNamingPolicy,
    RunnerNamingPolicy,
    TransformNamingPolicy,
)
from tiozin.exceptions import PolicyViolationError


# ============================================================================
# Testing PolicyDecision
# ============================================================================
def test_policy_decision_allow_should_pass_for_allow_decision():
    # Arrange
    decision = PolicyDecision.ALLOW

    # Act
    result = decision.allow()

    # Assert
    actual = result
    expected = True
    assert actual == expected


@pytest.mark.parametrize(
    "decision",
    [PolicyDecision.DENY, PolicyDecision.SKIP],
)
def test_policy_decision_allow_should_reject_non_allow_decisions(decision: PolicyDecision):
    # Act
    result = decision.allow()

    # Assert
    actual = result
    expected = False
    assert actual == expected


def test_policy_decision_deny_should_pass_for_deny_decision():
    # Arrange
    decision = PolicyDecision.DENY

    # Act
    result = decision.deny()

    # Assert
    actual = result
    expected = True
    assert actual == expected


@pytest.mark.parametrize(
    "decision",
    [PolicyDecision.ALLOW, PolicyDecision.SKIP],
)
def test_policy_decision_deny_should_reject_non_deny_decisions(decision):
    # Act
    result = decision.deny()

    # Assert
    actual = result
    expected = False
    assert actual == expected


def test_policy_decision_skip_should_pass_for_skip_decision():
    # Arrange
    decision = PolicyDecision.SKIP

    # Act
    result = decision.skip()

    # Assert
    actual = result
    expected = True
    assert actual == expected


@pytest.mark.parametrize(
    "decision",
    [PolicyDecision.ALLOW, PolicyDecision.DENY],
)
def test_policy_decision_skip_should_reject_non_skip_decisions(decision):
    # Act
    result = decision.skip()

    # Assert
    actual = result
    expected = False
    assert actual == expected


# ============================================================================
# Testing PolicyResult
# ============================================================================
def test_policy_result_ok_should_pass_when_decision_is_allowed():
    # Arrange
    policy_result = PolicyResult(policy=InputNamingPolicy, decision=PolicyDecision.ALLOW)

    # Act
    result = policy_result.ok()

    # Assert
    actual = result
    expected = True
    assert actual == expected


def test_policy_result_ok_should_reject_when_decision_is_skipped():
    # Arrange
    policy_result = PolicyResult(
        policy=InputNamingPolicy,
        decision=PolicyDecision.SKIP,
        message="Skipped for testing",
    )

    # Act
    result = policy_result.ok()

    # Assert
    actual = result
    expected = False
    assert actual == expected


def test_policy_result_ok_should_raise_error_when_decision_is_denied():
    # Arrange
    policy_result = PolicyResult(
        policy=InputNamingPolicy,
        decision=PolicyDecision.DENY,
        message="Denied for testing",
    )

    # Act & Assert
    with pytest.raises(PolicyViolationError) as exc_info:
        policy_result.ok()

    actual = exc_info.value.message
    expected = "InputNamingPolicy: Denied for testing."
    assert actual == expected


def test_policy_result_ok_should_use_default_message_when_denied_without_reason():
    # Arrange
    policy_result = PolicyResult(policy=InputNamingPolicy, decision=PolicyDecision.DENY)

    # Act & Assert
    with pytest.raises(PolicyViolationError) as exc_info:
        policy_result.ok()

    actual = exc_info.value.message
    expected = "InputNamingPolicy: Execution was denied."
    assert actual == expected


# ============================================================================
# Testing ProviderNamePolicy
# ============================================================================
@pytest.mark.parametrize(
    "provider_name",
    ["tio_my_provider", "tia_my_provider"],
)
def test_provider_name_policy_should_allow_name_with_valid_prefix(provider_name: str):
    # Arrange
    provider = Mock(spec=EntryPoint)
    provider.name = provider_name
    provider.value = f"test.{provider_name}"

    # Act
    result = FamilyNamePolicy.eval(provider)

    # Assert
    actual = result.decision
    expected = PolicyDecision.ALLOW
    assert actual == expected


@pytest.mark.parametrize(
    "provider_name,provider_value",
    [
        ("tio_my_provider", "my.namespace.tia_my_provider"),
        ("tia_my_provider", "my.namespace.tio_my_provider"),
    ],
)
def test_provider_name_policy_should_skip_package_with_valid_but_swapped_prefix(
    provider_name, provider_value
):
    # Arrange
    provider = Mock(spec=EntryPoint)
    provider.name = provider_name
    provider.value = provider_value

    # Act
    result = FamilyNamePolicy.eval(provider)

    # Assert
    actual = result.decision
    expected = PolicyDecision.SKIP
    assert actual == expected


def test_provider_name_policy_should_skip_name_without_valid_prefix():
    # Arrange
    provider = Mock(spec=EntryPoint)
    provider.name = "my_provider"
    provider.value = "some.package.my_provider"

    # Act
    result = FamilyNamePolicy.eval(provider)

    # Assert
    actual = result.decision
    expected = PolicyDecision.SKIP
    assert actual == expected


@pytest.mark.parametrize(
    "provider_name",
    ["tio_my_provider", "tia_my_provider"],
)
def test_provider_name_policy_should_skip_package_without_provider_name_suffix(
    provider_name,
):
    # Arrange
    provider = Mock(spec=EntryPoint)
    provider.name = provider_name
    provider.value = "some.package.wrong_name"

    # Act
    result = FamilyNamePolicy.eval(provider)

    # Assert
    actual = result.decision
    expected = PolicyDecision.SKIP
    assert actual == expected


# ============================================================================
# Testing InputNamingPolicy
# ============================================================================
@pytest.mark.parametrize(
    "name",
    [
        "MyInput",
        "DataSource",
        "FileReader",
    ],
)
def test_input_naming_policy_should_allow_name_with_valid_suffix(name):
    # Act
    result = InputNamingPolicy.eval(name)

    # Assert
    actual = result.decision
    expected = PolicyDecision.ALLOW
    assert actual == expected


@pytest.mark.parametrize(
    "name",
    [
        "MyInvalidInput_",
        "InvalidData",
        "BadName",
    ],
)
def test_input_naming_policy_should_skip_name_with_invalid_suffix(name):
    # Act
    result = InputNamingPolicy.eval(name)

    # Assert
    actual = result.decision
    expected = PolicyDecision.SKIP
    assert actual == expected


def test_input_naming_policy_should_show_name_in_skip_message():
    # Arrange
    name = "InvalidInput_"

    # Act
    result = InputNamingPolicy.eval(name)

    # Assert
    actual = "InvalidInput_" in result.message
    expected = True
    assert actual == expected


# ============================================================================
# Testing OutputNamingPolicy
# ============================================================================
@pytest.mark.parametrize(
    "name",
    [
        "MyOutput",
        "DataSink",
        "FileWriter",
    ],
)
def test_output_naming_policy_should_allow_name_with_valid_suffix(name):
    # Act
    result = OutputNamingPolicy.eval(name)

    # Assert
    actual = result.decision
    expected = PolicyDecision.ALLOW
    assert actual == expected


@pytest.mark.parametrize(
    "name",
    [
        "MyInvalidOutput_",
        "InvalidData",
        "BadName",
    ],
)
def test_output_naming_policy_should_skip_name_with_invalid_suffix(name):
    # Act
    result = OutputNamingPolicy.eval(name)

    # Assert
    actual = result.decision
    expected = PolicyDecision.SKIP
    assert actual == expected


def test_output_naming_policy_should_show_name_in_skip_message():
    # Arrange
    name = "InvalidOutput_"

    # Act
    result = OutputNamingPolicy.eval(name)

    # Assert
    actual = "InvalidOutput_" in result.message
    expected = True
    assert actual == expected


# ============================================================================
# Testing TransformNamingPolicy
# ============================================================================
@pytest.mark.parametrize(
    "name",
    [
        "MyTransform",
        "DataTransformer",
        "MyMapper",
        "DataProcessor",
    ],
)
def test_transform_naming_policy_should_allow_name_with_valid_suffix(name):
    # Act
    result = TransformNamingPolicy.eval(name)

    # Assert
    actual = result.decision
    expected = PolicyDecision.ALLOW
    assert actual == expected


@pytest.mark.parametrize(
    "name",
    [
        "MyInvalidTransform_",
        "InvalidData",
        "BadName",
    ],
)
def test_transform_naming_policy_should_skip_name_with_invalid_suffix(name):
    # Act
    result = TransformNamingPolicy.eval(name)

    # Assert
    actual = result.decision
    expected = PolicyDecision.SKIP
    assert actual == expected


def test_transform_naming_policy_should_show_name_in_skip_message():
    # Arrange
    name = "InvalidTransform_"

    # Act
    result = TransformNamingPolicy.eval(name)

    # Assert
    actual = "InvalidTransform_" in result.message
    expected = True
    assert actual == expected


# ============================================================================
# Testing RunnerNamingPolicy
# ============================================================================
@pytest.mark.parametrize(
    "name",
    [
        "MyRunner",
        "MyRuntime",
    ],
)
def test_runner_naming_policy_should_allow_name_with_valid_suffix(name):
    # Act
    result = RunnerNamingPolicy.eval(name)

    # Assert
    actual = result.decision
    expected = PolicyDecision.ALLOW
    assert actual == expected


@pytest.mark.parametrize(
    "name",
    [
        "MyInvalidRunner_",
        "InvalidData",
        "BadName",
    ],
)
def test_runner_naming_policy_should_skip_name_with_invalid_suffix(name):
    # Act
    result = RunnerNamingPolicy.eval(name)

    # Assert
    actual = result.decision
    expected = PolicyDecision.SKIP
    assert actual == expected


def test_runner_naming_policy_should_show_name_in_skip_message():
    # Arrange
    name = "InvalidRunner_"

    # Act
    result = RunnerNamingPolicy.eval(name)

    # Assert
    actual = "InvalidRunner_" in result.message
    expected = True
    assert actual == expected


# ============================================================================
# Testing RegistryNamingPolicy
# ============================================================================
def test_registry_naming_policy_should_allow_name_with_valid_suffix():
    # Arrange
    name = "MyRegistry"

    # Act
    result = RegistryNamingPolicy.eval(name)

    # Assert
    actual = result.decision
    expected = PolicyDecision.ALLOW
    assert actual == expected


@pytest.mark.parametrize(
    "name",
    [
        "MyInvalidRegistry_",
        "InvalidData",
        "BadName",
    ],
)
def test_registry_naming_policy_should_skip_name_with_invalid_suffix(name):
    # Act
    result = RegistryNamingPolicy.eval(name)

    # Assert
    actual = result.decision
    expected = PolicyDecision.SKIP
    assert actual == expected


def test_registry_naming_policy_should_show_name_in_skip_message():
    # Arrange
    name = "InvalidRegistry_"

    # Act
    result = RegistryNamingPolicy.eval(name)

    # Assert
    actual = "InvalidRegistry_" in result.message
    expected = True
    assert actual == expected
