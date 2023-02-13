# ModusToolbox Manifest Checker

### Overview
This project contains a suite of tests for the purpose of validating the ModusToolbox manifest files.

Perform the default suite of tests by running:<br>
`    ./mtb_manifest_checker.sh    `<br>
which is the same as running:<br>
`    ./mtb_manifest_checker.sh --syntax --format --schema --assets https://github.com/Infineon/mtb-super-manifest/raw/v2.X/mtb-super-manifest-fv2.xml    `

Perform all tests in the suite, except the "format" tests, by running:<br>
`    ./mtb_manifest_checker.sh --syntax --schema --assets    `

Perform the "format" tests only, by running:<br>
`    ./mtb_manifest_checker.sh --format    `

Perform the "syntax" tests only on a specified set of local manifest files, by running:<br>
`    ./mtb_manifest_checker.sh --syntax apps/*.xml bsp/*.xml mw/*.xml    `

### Syntax
`    mtb-manifest_checker.sh [--syntax] [--format] [--schema] [--assets] [ <uri_of_super-manifest_file> | <pathname_of_manifest_file> [...] ]    `<br>
- where:
    - "--syntax" is the Syntax Checker (details at 'documentation/syntax.md')
    - "--format" is the Format Checker (details at 'documentation/format.md')
    - "--schema" is the Schema Checker (details at 'documentation/schema.md')
    - "--assets" is the Assets Checker (details at 'documentation/assets.md')
    - (optional) <uri_of_super-manifest_file> is the URI of the super-manifest file
    - (optional) <pathname_of_manifest_file> is one or more manifest files; wildcards are acceptable

1. note that <uri_of_super-manifest_file> and <pathname_of_manifest_file> are exclusive; cannot specify both on the command line
2. note that "dependency" manifest files must be processed last, therefore:<br>
    - if a super-manifest URI is specified (or the default URI is used), then all manifest files that it references will be processed in the appropriate order.
    - if multiple manifest files are specified, then all manifest files will be processed in the appropriate order.

### Requirements
- Tools
    - xmllint
    - Python 3
- Python 3 modules (see: 'requirements.txt')
    - lxml
    - requests

### Supported Environments
- Linux
    - tested on "Ubuntu 20.04.5 LTS"
- Mac
    - tested on "macOS Catalina 10.15.7"
    - tested on "macOS Big Sur 11.6.5"
    - tested on "macOS Monterey 12.3"
- Windows
    - tested on "cygwin (CYGWIN_NT-10.0-19042 version 3.1.6-340.x86_64)"
