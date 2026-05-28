# NUnit Test Rules

## Coverage Requirement

Every changed function must have both:
- Positive test coverage.
- Negative test coverage.

Both must pass before push can be allowed.

## Positive Tests

Positive tests should cover:
- Typical valid input.
- Required customer/package/site combinations when relevant.
- Expected return values, state changes, or output DTO fields.
- Successful external dependency handling using mocks/fakes if the repo already uses them.

## Negative Tests

Negative tests should cover at least one relevant invalid scenario:
- Null input.
- Empty string or empty collection.
- Boundary value.
- Invalid enum/code.
- Customer not allowed.
- Package not allowed.
- Missing required data.
- Expected exception.

## Naming

Follow the repo's existing test naming. If absent, use:

```text
FunctionName_Condition_ExpectedResult
```

Examples:

```csharp
[Test]
public void CalculateFee_ValidPackage_ReturnsFee()

[Test]
public void CalculateFee_UnknownPackage_ThrowsArgumentException()
```

## Gate Rules

Do not treat these as pass:
- Missing generated test body.
- `Assert.Pass()` with no behavioral assertion.
- `Assert.Inconclusive(...)`.
- Comment-only test skeleton.
- Tests that are generated but not included in the test project.
