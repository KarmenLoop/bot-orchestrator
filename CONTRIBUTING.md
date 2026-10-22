# Contributing

Thank you for helping make agent work more accountable and easier to resume.

## Before opening an issue

Read the relevant guide and reproduce the behavior in a disposable workspace. Include the command, Python version, operating system, expected result, actual result, and a sanitized error or output. Never attach a real account token, private transcript, or task database containing sensitive work.

## Development setup

Clone the repository and use Python 3.9 or newer. No package installation is needed for the included tools.

```bash
python3 -B skills/bot-orchestrator/scripts/test_board.py
python3 -B skills/bot-orchestrator/scripts/test_moa.py
python3 -B scripts/test_repository.py
python3 scripts/check_repository.py
python3 examples/local_demo.py
python3 examples/moa_demo.py
python3 scripts/validate.py --repeat 3 --output /absolute/path/to/new-validation-directory
```

Keep English and Simplified Chinese README and tutorial counterparts aligned. Use English for code, example data, comments, UI metadata, and concrete commit messages.

## Pull requests

Keep changes focused on one observable problem or capability. Explain:

1. The concrete case that fails or is unnecessarily difficult.
2. The resulting behavior and any lifecycle or storage changes.
3. The actual verification commands and results.
4. Any platform or integration that remains untested.

Behavior changes should include a meaningful regression case. Test real observable behavior rather than matching the implementation's wording. Preserve failure cases and do not weaken assertions to make a change pass.

Changes to the board must keep submission separate from acceptance, preserve atomic state transitions, reject unsupported schemas, and retain honest evidence semantics. Execution behavior belongs only in the opt-in command driver; preserve its bounded protocol, immutable candidate evidence, full verifier coverage, and failure history. Schedulers, account authorities, and model clients do not belong in the core board.

## Skill changes

Keep the entry point concise enough to load during a real task. Put conditional detail in a linked reference. Preserve already-granted user scope without treating it as permission for new external actions. Do not require a particular host tool unless the workflow actually depends on it and its availability is documented.

When reporting compatibility, identify the host version, import method, invocation, tools exercised, actual outcome, and remaining limits. A screenshot of a skill listing is not evidence that a connector or background process works.

## Licensing

Contributions are accepted under this repository's MIT License. Submit only material you have the right to contribute. Disclose third-party code or assets and include applicable notices. There is no separate contributor license agreement in this repository.

## Conduct

Follow the [Code of Conduct](CODE_OF_CONDUCT.md). Discuss observable behavior and proposed fixes respectfully.

## Documentation and release changes

Keep the English and Simplified Chinese entry pages and guides aligned. Explain the reader’s actual task with project-specific examples. Use concrete English commit subjects. New ordinary filenames and versioned release assets use lowercase kebab-case without spaces; conventional README, LICENSE, SKILL and metadata names remain unchanged. Before release, compare each package, version label, command, and current image with the documented behavior. Label diagrams, synthetic data, historical evidence, and unverified integrations accurately.
