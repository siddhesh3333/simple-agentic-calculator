"""Safe calculator operations used by the AI agent."""

import math
from numbers import Real


class CalculatorError(ValueError):
    """Raised when a calculator request cannot be completed safely."""


SUPPORTED_OPERATIONS = {
    "addition",
    "subtraction",
    "multiplication",
    "division",
    "percentage",
    "power",
    "square_root",
}


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise CalculatorError(f"{name} must be a number.")
    result = float(value)
    if not math.isfinite(result):
        raise CalculatorError(f"{name} must be a finite number.")
    return result


def calculate(operation: str, a: object, b: object | None = None) -> float:
    """Perform one explicitly supported operation without using eval()."""
    if not isinstance(operation, str) or not operation.strip():
        raise CalculatorError("The operation cannot be empty.")

    operation = operation.strip().lower()
    if operation not in SUPPORTED_OPERATIONS:
        raise CalculatorError(f"Unsupported operation: {operation}.")

    first = _number(a, "a")

    if operation == "square_root":
        if first < 0:
            raise CalculatorError("Cannot take the square root of a negative number.")
        return math.sqrt(first)

    if b is None:
        raise CalculatorError(f"Operation '{operation}' requires a second number.")
    second = _number(b, "b")

    if operation == "addition":
        return first + second
    if operation == "subtraction":
        return first - second
    if operation == "multiplication":
        return first * second
    if operation == "division":
        if second == 0:
            raise CalculatorError("Division by zero is not allowed.")
        return first / second
    if operation == "percentage":
        return (first / 100) * second
    if operation == "power":
        try:
            result = first**second
        except (OverflowError, ValueError):
            raise CalculatorError("That power operation is too large or invalid.")
        if not math.isfinite(result):
            raise CalculatorError("The power result is not finite.")
        return result

    # The operation set is checked above; this is defensive if it changes later.
    raise CalculatorError(f"Unsupported operation: {operation}.")
