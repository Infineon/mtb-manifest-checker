'''
# Copyright 2019-2022, Cypress Semiconductor Corporation (an Infineon company) or
# an affiliate of Cypress Semiconductor Corporation.  All rights reserved.
#
# This software, including source code, documentation and related
# materials ("Software") is owned by Cypress Semiconductor Corporation
# or one of its affiliates ("Cypress") and is protected by and subject to
# worldwide patent protection (United States and foreign),
# United States copyright laws and international treaty provisions.
# Therefore, you may use this Software only as provided in the license
# agreement accompanying the software package from which you
# obtained this Software ("EULA").
# If no EULA applies, Cypress hereby grants you a personal, non-exclusive,
# non-transferable license to copy, modify, and compile the Software
# source code solely for use in connection with Cypress's
# integrated circuit products.  Any reproduction, modification, translation,
# compilation, or representation of this Software except as specified
# above is prohibited without the express written permission of Cypress.
#
# Disclaimer: THIS SOFTWARE IS PROVIDED AS-IS, WITH NO WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, NONINFRINGEMENT, IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. Cypress
# reserves the right to make changes to the Software without notice. Cypress
# does not assume any liability arising out of the application or use of the
# Software or any product or circuit described in the Software. Cypress does
# not authorize its products for use in any products where a malfunction or
# failure of the Cypress product may reasonably be expected to result in
# significant property damage, injury or death ("High Risk Product"). By
# including Cypress's product in a High Risk Product, the manufacturer
# of such system or application assumes all risk of such use and in doing
# so agrees to indemnify Cypress against all liability.
'''
import sys
import os
import operator
import urllib.request, urllib.error, urllib.parse
import errno
from xml.parsers import expat

try:
    from lxml import etree
except ImportError as ex:
    raise ImportError(
"""
**** please run: ****
  pip install -r requirements.txt
    - 'requirements.txt' is located in the same folder as validate_schema.py
********
)
"""
)

xml_validation_result = {"valid": "Valid manifest",
                         "invalid": "Invalid manifest"}

SCHEMA_NAME_TEMPLATE = "schema_{}.xsd"


class Args(object):
    # class which handle inputs

    # parameters
    expected_manifest = ["app", "board", "middleware", "dependency", "super"]
    expected_args_quantity = 2
    manifest_type = property(operator.attrgetter('_manifest_type'))
    xml_path = property(operator.attrgetter('_xml_path'))

    @manifest_type.setter
    def manifest_type(self, value):

        # check if not empty
        if not value:
            raise Exception("manifest_type cannot be empty.")

        # check if allowed
        if value not in self.expected_manifest:
            raise Exception("manifest_type value is not expected. GIVEN: {}. EXPECTED: {}."
                            .format(value, ', '.join(self.expected_manifest)))

        # assign value
        self._manifest_type = value

    @xml_path.setter
    def xml_path(self, value):
        if not value:
            raise Exception("xml_path cannot be empty.")
        self._xml_path = value

    def __init__(self):
        # skip first arg which is this file name
        args = sys.argv[1:]

        # check expected quantity of inputs
        if len(args) != self.expected_args_quantity:
            raise Exception("Expected: {} args. Provided({}): {} "
                            .format(self.expected_args_quantity, len(args), ', '.join(args)))

        # set parameters
        self.manifest_type = args[0]
        self.xml_path = args[1]


class XmlValidator(object):
    # class which handles validation

    # properties
    xml_schema = property(operator.attrgetter('_xml_schema'))
    # temp var to store encoding
    encoding = ""
    # lowercase expected
    allowed_xml_encoding = ["utf-8"]

    def __init__(self, manifest_type):
        self.xml_schema = manifest_type

    @xml_schema.setter
    def xml_schema(self, manifest_type):
        # read the schema file
        schema_file = "{}/schema_{}.xsd".format(os.path.dirname(__file__), manifest_type)
        try:
            with open(schema_file, 'rb') as schema:
                schema = schema.read()

        except Exception as ex:
            raise Exception(str(ex))

        # check encoding
        self.check_encoding(schema)

        # assign schema
        self._xml_schema = etree.XMLSchema(etree.fromstring(schema))


    def check_encoding(self, path_to_file):
        current_encoding = self.get_xml_encoding(path_to_file).lower()
        if not current_encoding:
            raise Exception("File '{}' has no encoding info"
                            .format(path_to_file, current_encoding))
        elif not current_encoding in self.allowed_xml_encoding:
            raise Exception("File '{}' has '{}' encoding. Allowed {}"
                            .format(path_to_file, current_encoding, ", ".join(self.allowed_xml_encoding)))

    def get_xml_encoding(self, xml):
        self.parse_xml_header(xml)
        return self.encoding

    def xml_decl_handler(self, version, encoding, standalone):
        self.encoding = encoding

    def parse_xml_header(self, xml):
        parser = expat.ParserCreate()
        parser.XmlDeclHandler = self.xml_decl_handler
        parser.Parse(xml)

    def validate_manifest(self, xml_path, verbose=1):

        print("")
        if os.path.isfile(xml_path):
            xml_manifest_file = xml_path
        elif os.path.isdir(xml_path):
            """ TODO: implement logic for folder """
            raise NotImplementedError
        else:
            raise Exception("File \"{}\" does not exist".format(xml_path))

        # read xml manifest
        with open(xml_manifest_file, 'r') as xml_manifest:
            xml_manifest = xml_manifest.read()
        try:
            # check encoding
            self.check_encoding(xml_manifest)

            # verify xml schema
            validation_result = self.xml_schema.validate(etree.fromstring(xml_manifest.encode("UTF-8")))
            if validation_result:
                if verbose >= 1:
                    print((xml_validation_result["valid"]))
                    print(("Manifest: {}".format(xml_manifest_file)))
                    print("passed schema and data integrity validation")
            else:
                self.xml_schema.assertValid(etree.fromstring(xml_manifest.encode("UTF-8")))
            return validation_result

        except (etree.DocumentInvalid, etree.XMLSyntaxError, expat.ExpatError) as ex:
            print((xml_validation_result["invalid"]))
            print(("Manifest: {}".format(xml_manifest_file)))
            print(("Message: {}".format(ex.args[0])))
            raise SystemExit(1)


def main():
    # main method
    args = Args()
    xml_validator = XmlValidator(args.manifest_type)
    return xml_validator.validate_manifest(args.xml_path)


if __name__ == '__main__':
    main()
