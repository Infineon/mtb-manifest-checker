# ModusToolbox Manifest Checker -- format

### Overview
The "format" checker is part of the suite of tests for the purpose of validating the ModusToolbox manifest files.

It is invoked by running:<br>
`    ./mtb_manifest_checker.sh --format    `<br>
and it is included in the default test suite, when no other options are specified.

### Details
The "format" checker:
- runs `xmllint --format`,
- saves the output to a temporary file,
- post-processes this file to handle the exceptions (listed below), and
- performs a `diff` between the original file and the temporary file
    - any differences in these files is considered a failure

Note: `xmllint` is an industry standard tool for validating XML files.<br>
For more information, see: http://www.xmlsoft.org/<br>
To install, perhaps run: `sudo apt install libxml2-utils`

### Execeptions
There are some desired exceptions to the standard `xmllint --format` which have been implemented:
1. the "XML declaration" line (first line in the XML file) is removed
    - although usually required in a properly formatted XML file, ModusToolbox manifest files do not contain this XML declaration line
2. allow blank lines
    - although usually not allowed in a properly formatted XML file, ModusToolbox manifest files allow blank lines to increase readability
3. specify some special characters in decimal, rather than hex
    - although a properly formatted XML file requires special characters to be specified in hexadecimal, for historical reasons, ModusToolbox manifest files use decimal for some of the special characters
        - the following special character use decimal:

| symbol | hex | dec |
| - | - | - |
| &#x2122; | #x2122 | #8482 |
| &#xAE; | #xAE | #174 |
| &#xB1; | #xB1 | #177 |

### Tip
After `./mtb_manifest_checker.sh --format` is run, the temporary file is saved in the "./out" directory; this file may be used to replace the original XML file if there are formatting errors.
