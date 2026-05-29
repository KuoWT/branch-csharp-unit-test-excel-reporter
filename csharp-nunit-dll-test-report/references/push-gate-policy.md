# Push Gate Policy

The skill reports whether push is allowed. It must not push unless the user explicitly asks.

Push allowed requires:

1. Restore passes.
2. Build passes.
3. NUnit test command passes.
4. Every changed function has a positive test.
5. Every changed function has a negative test.
6. All positive and negative tests pass.
7. Positive and negative input/output descriptions are present.
8. HTML report is generated.

Output one of:

```text
PASS: 可 push
```

```text
FAIL: 不可 push
```

When failed, list the blocking items and point to the HTML report.
