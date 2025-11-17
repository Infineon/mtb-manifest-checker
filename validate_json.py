'''
# (c) 2023-2025, Infineon Technologies AG, or an affiliate of Infineon
# Technologies AG. All rights reserved.
# This software, associated documentation and materials ("Software") is
# owned by Infineon Technologies AG or one of its affiliates ("Infineon")
# and is protected by and subject to worldwide patent protection, worldwide
# copyright laws, and international treaty provisions. Therefore, you may use
# this Software only as provided in the license agreement accompanying the
# software package from which you obtained this Software. If no license
# agreement applies, then any use, reproduction, modification, translation, or
# compilation of this Software is prohibited without the express written
# permission of Infineon.
# 
# Disclaimer: UNLESS OTHERWISE EXPRESSLY AGREED WITH INFINEON, THIS SOFTWARE
# IS PROVIDED AS-IS, WITH NO WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING, BUT NOT LIMITED TO, ALL WARRANTIES OF NON-INFRINGEMENT OF
# THIRD-PARTY RIGHTS AND IMPLIED WARRANTIES SUCH AS WARRANTIES OF FITNESS FOR A
# SPECIFIC USE/PURPOSE OR MERCHANTABILITY.
# Infineon reserves the right to make changes to the Software without notice.
# You are responsible for properly designing, programming, and testing the
# functionality and safety of your intended application of the Software, as
# well as complying with any legal requirements related to its use. Infineon
# does not guarantee that the Software will be free from intrusion, data theft
# or loss, or other breaches ("Security Breaches"), and Infineon shall have
# no liability arising out of any Security Breaches. Unless otherwise
# explicitly approved by Infineon, the Software may not be used in any
# application where a failure of the Product or any consequences of the use
# thereof can reasonably be expected to result in personal injury.
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
