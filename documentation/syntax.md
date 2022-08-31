# ModusToolbox Manifest Checker -- syntax

### Overview
The "syntax" checker is part of the suite of tests for the purpose of validating the ModusToolbox manifest files.

It is invoked by running:<br>
`    ./mtb_manifest_checker.sh --syntax    `<br>
and it is included in the default test suite, when no other options are specified.

### Details
The "syntax" checker runs `xmllint` (with no options).

Note: `xmllint` is an industry standard tool for validating XML files.<br>
For more information, see: http://www.xmlsoft.org/<br>
To install, perhaps run: `sudo apt install libxml2-utils`
