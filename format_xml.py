'''
# Copyright 2022-2025, Cypress Semiconductor Corporation (an Infineon company) or
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
