# ModusToolbox Manifest Checker -- schema

### Overview
The "schema" checker is part of the suite of tests for the purpose of validating the ModusToolbox manifest files.

It is invoked by running:<br>
`    ./mtb_manifest_checker.sh --schema    `<br>
and it is included in the default test suite, when no other options are specified.

### Details
The "schema" checker runs the `validate_schema.py` script, which
- processes the specified manifest file, and
- verifies the specific schema (super, board, middleware, app, or dependency) for that XML file.
