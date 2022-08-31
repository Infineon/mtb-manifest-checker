# ModusToolbox Manifest Checker -- assets

### Overview
The "assets" checker is part of the suite of tests for the purpose of validating the ModusToolbox manifest files.

It is invoked by running:<br>
`    ./mtb_manifest_checker.sh --assets    `<br>
and it is included in the default test suite, when no other options are specified.

### Details
The "assets" checker runs the `validate_assets.py` script, which
- processes the elements from the specified manifest file, and
- verifies that every required reference ( branch, tag, or commit ) is accessible at that required URL.

This tests both
- access to the URL, and
- the existence of the reference at that URL
    - errors with either step is considered a failure

The `git ls-remote` command is used to determine if a branch (refs/heads) or a tag (refs/tags) exists on the upstream remote.<br>
If the `git ls-remote` output does not contain the required reference, then the "bare repo" is downloaded from the upstream remote to a temporary directory,<br>
and the `git branch -a --contains` command is used to find the reference in that repo.
