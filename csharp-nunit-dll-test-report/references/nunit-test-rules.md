# NUnit Test Rules

## Coverage Requirement

Every changed function must have both:
- Positive test coverage.
- Negative test coverage.
- Positive and negative input descriptions.
- Positive and negative output descriptions.

Both must pass before push can be allowed.

Coverage checks apply only to `.cs` files/functions changed in the tag-to-branch diff. Tests for unchanged functions or non-`.cs` files may exist, but they must not be counted as coverage for the report gate.

If the diff contains no `.cs` changes, do not create placeholder test cases. The report test items should remain empty.

## Test Project Placement

If a suitable NUnit test project already exists, add the new tests there.

If no suitable NUnit test project exists:

1. Create a new NUnit project under `tests/<DllProject>.Tests`.
2. Add a project reference to the changed DLL project.
3. Add the test project to the solution when a `.sln` exists.
4. Mirror the changed production path under a `DiffCoverage` folder.

Example:

```text
src/BillingDll/FeeCalculator.cs
tests/BillingDll.Tests/DiffCoverage/src/BillingDll/FeeCalculatorTests.cs
```

## Positive Tests

Positive tests should cover:
- Typical valid input.
- Required customer/package/site combinations when relevant.
- Expected return values, state changes, or output DTO fields.
- Successful external dependency handling using mocks/fakes if the repo already uses them.
- A clear input description and expected output description for the HTML report.

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
- A clear invalid input description and expected error/exception output description for the HTML report.

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
