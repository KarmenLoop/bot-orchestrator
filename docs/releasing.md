# Release process

This is a maintainer checklist, not evidence that a release already exists.

## Prepare

1. Choose the version in `VERSION` and the skill's frontmatter metadata.
2. Update `CHANGELOG.md` with actual behavior and compatibility changes.
3. Run the board tests, repository-tool tests, repository checker, and both repository and standalone demonstrations. Validate the skill entry format with the host tooling when available.
4. Inspect the exact files to publish. Exclude task databases, generated workspaces, credentials, local paths, and private evidence.
5. Keep root and standalone-skill license files identical.

## Publish

Push the reviewed source through the intended authenticated GitHub account. If creating a tag or GitHub Release, verify that it points to the reviewed commit and that attached archives contain the expected skill files and license.

Do not claim a release download, CI pass, platform acceptance, or host integration without an actual corresponding result. The source ZIP from GitHub's Code menu is available separately from a maintainer-created release asset.

## Compatibility notes

Treat board schema changes as explicit migration work. Do not make initialization silently overwrite an old board. Describe new host integrations by the actions actually exercised rather than by a skill-listing screenshot.
