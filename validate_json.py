'''
# Copyright 2023-2025, Cypress Semiconductor Corporation (an Infineon company) or
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

import filecmp
import json
import sys

if len(sys.argv) < 3:
    print('FATAL ERROR: must have at least 2 args!', file=sys.stderr)
    exit(1)

arg1 = sys.argv[1]
file_name = sys.argv[2]

def syntax_json(file_obj):
    try:
        json.load(file_obj)
    except ValueError as err:
        return False
    return True

def format_json(file_obj, tmp_file):
    json_dict = json.load(file_obj)
    json_obj = json.dumps(json_dict, indent=3)
    with open(tmp_file, 'w', newline='') as file:
        # override os.linesep; do not generate '\r'
        file.write(json_obj)
        file.write('\n')

if arg1 == "--syntax":
    with open(file_name, 'r') as file:
        if not syntax_json(file):
            exit(2)

elif arg1 == "--format":
    if len(sys.argv) != 4:
        print('FATAL ERROR: "--format" must have 3 args!', file=sys.stderr)
        exit(1)
    out_file=sys.argv[3]
    with open(file_name, 'r') as file:
        format_json(file, out_file)
    if not filecmp.cmp(file_name, out_file):
        exit(3)

else:
    print('FATAL ERROR: invalid argument [{}]'.format( arg1 ), file=sys.stderr)
    exit(4)

exit(0)
