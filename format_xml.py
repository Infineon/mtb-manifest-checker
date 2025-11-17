'''
# (c) 2022-2025, Infineon Technologies AG, or an affiliate of Infineon
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

# keep blank lines in the generated XML file

import sys

if len(sys.argv) < 3:
    print('FATAL ERROR: must have at least 2 arg!', file=sys.stderr)
    exit(1)

file1 = sys.argv[1]
file2 = sys.argv[2]

output = []

with open(file1, 'r') as file:
    lines1 = file.readlines()

with open(file2, 'r') as file:
    lines2 = file.readlines()

idx1 = 0
idx2 = 0
max_lines = len(lines1) + 1000
for i in range(max_lines):
    line1 = ""
    if idx1 < len(lines1):
        line1 = lines1[idx1]
    line2 = ""
    if idx2 < len(lines2):
        line2 = lines2[idx2]
    if not line1 and not line2:
        # done
        break
    if not line1.rstrip() and not line2.rstrip():
        # both have blank lines
        output.append("\n")
        idx1 += 1
        idx2 += 1
    elif not line1.rstrip():
        # detected blank line
        output.append("\n")
        idx1 += 1
    else:
        # use formatted line
        output.append(line2)
        idx1 += 1
        idx2 += 1

with open(file2, 'w', newline='') as file:
    # override os.linesep; do not generate '\r'
    for x in output:
        file.write(x)
