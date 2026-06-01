# Push Gate Policy

The skill reports whether push is allowed. It must not push unless the user explicitly asks.

Push allowed requires:

1. HTML report is generated.
2. Build passes.
3. If there are no testable C# function changes, no positive/negative test coverage is required.
4. If there are testable C# function changes, NUnit test command passes.
5. If there are testable C# function changes, every changed function has a positive test.
6. If there are testable C# function changes, every changed function has a negative test.
7. If there are testable C# function changes, all positive and negative tests pass.
8. If there are testable C# function changes, positive and negative input/output descriptions are present.

Output one of:

```text
PASS: 可 push
```

```text
FAIL: 不可 push
```

When failed, list the blocking items and point to the HTML report.
