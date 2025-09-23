#!/bin/bash
##########
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
##########

restore_errexit=""
test -o errexit && restore_errexit="set -e"
restore_xtrace="set +x"
test -o xtrace && restore_xtrace="set -x"

export PYTHONUNBUFFERED=1

top_dir=${0%/*}

# default super-manifest
uri_super_manifest=https://github.com/Infineon/mtb-super-manifest/raw/v2.X/mtb-super-manifest-fv2.xml

legal_category_app=(
"Audio"
"Battery Charging"
"Bluetooth&#174;"
"Community Code Examples"
"Connectivity"
"Getting Started"
"Graphics"
"Industrial Communication"
"Machine Learning"
"Manufacturing"
"Motor Control"
"Peripherals"
"Power Conversion"
"Security"
"Sensing"
"Solutions"
"USB-C Power Delivery"
""
"Wi-Fi"
)

legal_category_bsp=(
"AIROC&#8482; Bluetooth&#174; BSPs"
"AIROC&#8482; Connectivity BSPs"
"CCG BSPs"
"iMOTION&#8482; BSPs"
"LITIX&#8482; BSPs"
"MOTIX&#8482; BSPs"
"PMG BSPs"
"PSOC&#8482; 4 BSPs"
"PSOC&#8482; 6 BSPs"
"PSOC&#8482; Control BSPs"
"PSOC&#8482; Edge BSPs"
"PSOC&#8482; Wireless BSPs"
"Reference Design BSPs"
"TRAVEO&#8482; BSPs"
"USB BSPs"
"Wireless Charging BSPs"
"XMC&#8482; BSPs"
)

legal_category_mw=(
"Bluetooth&#174;"
"Connectivity"
"Core"
"Ethernet"
"Graphics"
"Middleware"
"Motor Control"
"Peripheral"
"Power Conversion"
"Utilities"
"Voice"
"Wi-Fi"
)

g_manifest_type=""
g_failed=0

f_syntax=0
f_format=0
f_schema=0
f_assets=0
f_rules=0
f_flags=0
f_custom=0
manifest_files=()
manifest_uri=""
# parse command line args
while (( $# > 0 )); do
  case "$1" in
    "--syntax")
      f_syntax=1
      f_flags=1
      ;;
    "--format")
      f_format=1
      f_flags=1
      ;;
    "--schema")
      f_schema=1
      f_flags=1
      ;;
    "--assets")
      f_assets=1
      f_flags=1
      ;;
    "--rules")
      f_rules=1
      f_flags=1
      ;;
    "--custom")
      f_custom=1
      ;;
    "--"*)
      echo "FATAL ERROR: unknown argument $1"
      exit 2
      ;;
    *)
      arg=$1
      if [[ ${arg} = "https://"* || ${arg} = "http://"* ]]; then
        if [[ -z ${manifest_uri} ]]; then
          manifest_uri=${arg}
          uri_super_manifest=${manifest_uri}
        else
          echo "INFO: 'manifest uri' has already been specified [${manifest_uri}]"
          echo "FATAL ERROR: unhandled argument ${arg}"
          exit 2
        fi
      else
        lines=$(ls -d ${arg} 2>/dev/null) || :
        match=$(echo ${lines} | wc -l)
        if [[ ${match} -ne 0 ]]; then
          for x in $(echo ${lines}); do
            manifest_files+=(${x})
          done
        else
          echo "FATAL ERROR: the specified 'manifest file' (${arg}) does not exist"
          exit 3
        fi
      fi
      ;;
  esac
  shift
done

if [[ -n ${manifest_uri} && ${#manifest_files[@]} -ne 0 ]]; then
  echo "FATAL ERROR: cannot specify both a 'manifest uri' and 'manifest files'!"
  echo "INFO: 'manifest uri' [${manifest_uri}]"
  echo "INFO: 'manifest file(s)' [${manifest_files[@]}]"
  exit 2
fi


function requires_xmllint()
{
  found=$(which xmllint) || :
  if [[ -z ${found} ]]; then
    echo "FATAL ERROR: 'xmllint' is required!"
    echo " ... perhaps: sudo apt install libxml2-utils"
    exit 4
  fi
}

function requires_python3()
{
  PYTHON3=python3
  major_version=$(which python >/dev/null 2>&1 && python --version 2>&1 | tr -d '[a-zA-Z ]*' | cut -d '.' -f1)
  # use 'python' if it is version 3.x.x or above
  [[ ${major_version} -ge 3 ]] && PYTHON3=python

  found=$(which ${PYTHON3}) || :
  if [[ -z ${found} ]]; then
    echo "FATAL ERROR: 'python3' is required!"
    echo " ... perhaps: sudo apt install python3"
    exit 4
  fi

  printf "\n[info] using '%s' (%s) at [%s]\n\n" ${PYTHON3} $(${PYTHON3} --version 2>&1 | tr -d '[a-zA-Z ]*') $(which ${PYTHON3})
}

function requires_python3_module()
{
  module=$1
  set +e
  ${PYTHON3} -c "import ${module}" 2>/dev/null
  rc=$?
  ${restore_errexit}
  if [[ ${rc} -ne 0 ]]; then
    echo "FATAL ERROR: python3 module '${module}' is required!"
    echo " ... perhaps: pip install ${module}"
    exit 4
  fi
}

function read_xml()
{
  local IFS=\>
  read -r -d \< ENTITY CONTENT
  rc=$?
  return ${rc}
}

function detect_type()
{
  eval manifest_type='$'$1  # arg is variable name
  filename=$2

  line=$(head -1 ${filename})
  line="${line//$'\r'}"  # strip the '\r' character

  manifest_type=""
  [[ ${line} = '<apps>' ]]                          && manifest_type="app"
  [[ ${line} = '<apps version="2.0">' ]]            && manifest_type="app"
  [[ ${line} = '<boards>' ]]                        && manifest_type="board"
  [[ ${line} = '<dependencies>' ]]                  && manifest_type="dependency"
  [[ ${line} = '<dependencies version="2.0">' ]]    && manifest_type="dependency"
  [[ ${line} = '<middleware>' ]]                    && manifest_type="middleware"
  [[ ${line} = '<middleware version="2.0">' ]]      && manifest_type="middleware"
  [[ ${line} = '<super-manifest>' ]]                && manifest_type="super"
  [[ ${line} = '<super-manifest version="2.0">' ]]  && manifest_type="super"

  if [[ ${manifest_type} = "" ]]; then
    echo -e "\nFATAL ERROR: cannot determine 'manifest type' from '${line}' in '${filename}'"
  fi
  eval $1=${manifest_type}

  return 0
}

function validate_category()
{
  g_manifest_type=$1
  manifest_file=$2
# echo -e "+ grep \"<category>.*</category>\" ${manifest_file}"
#            grep  "<category>.*</category>"  ${manifest_file} || :
  #
  legal_values=()
  case "${g_manifest_type}" in
    "app")
      legal_values=("${legal_category_app[@]}")
      ;;
    "board")
      legal_values=("${legal_category_bsp[@]}")
      ;;
    "dependency")
      # no "category" element to process
      ;;
    "middleware")
      legal_values=("${legal_category_mw[@]}")
      ;;
    "super")
      # no "category" element to process
      ;;
    *)
      echo -e "\nFATAL ERROR: unknown manifest type: ${g_manifest_type}\n"
      g_failed=1
      ;;
  esac
  #
  failed=0
  is_partner=$(echo "${manifest_file}" | grep -v -i "^Infineon/" | wc -l)
  msg_prefix="FATAL ERROR"
  [[ ${is_partner} -ne 0 ]] && msg_prefix="Warning"
  ## readarray is not available pre Bash-4
  #readarray -t output < <(grep "<category>.*</category>" ${manifest_file})
  output=()
  while read line; do output+=("${line}"); done < <(grep "<category>.*</category>" ${manifest_file})
  ##
  for x in "${output[@]}"; do
    for y in "${legal_values[@]}"; do
      match=$(echo "${x}" | grep "^ *<category>${y}</category>$" | wc -l)
      [[ ${match} -ne 0 ]] && break
    done
    if [[ ${match} -eq 0 ]]; then
      echo -e "${msg_prefix}: unknown category: ${x}"
      failed=1
    fi
  done
  #
  if [[ ${failed} -eq 0 ]]; then
    echo "passed 'validate_category' check"
  else
    echo -e "\nnote: pre-defined categories (for \"${g_manifest_type}\" type manifest files) are:"
    for y in "${legal_values[@]}"; do
      echo "    ${y}"
    done
    if [[ ${is_partner} -eq 0 ]]; then
      echo "FATAL ERROR: invalid catagories"
      g_failed=1
    fi
  fi
  echo ""
}

function test_syntax()
{
  echo -e "\n\n########## test syntax ##########"
  requires_xmllint
  set +e
  echo "+ xmllint ${manifest_file} >/dev/null"
          xmllint ${manifest_file} >/dev/null
  rc=$?
  ${restore_errexit}
  if [[ ${rc} -eq 0 ]]; then
    echo ""
    echo "Manifest: ${manifest_file}"
    echo "passed syntax validation"
    echo ""
  else
    echo "xmllint returned: ${rc}"
    g_failed=1
  fi
  echo -e "####################"
}


function test_format()
{
  echo -e "\n\n########## test format ##########"
  requires_xmllint
  requires_python3
  echo "+ xmllint --format ${manifest_file} | 'post-process with custom format'"
  x=${manifest_file}
  y=${x##*/}
  rm -rf   out/${y}
  mkdir -p out
  #
  ## initial format the file
  set +e
  xmllint --format $x > out/$y
  rc=$?
  ${restore_errexit}
  #
  ## handle optional XML Declaration
  ## - delete the line in generated file, if XML declaration does not exist in original file
  s='<?xml version='
  [[ $(head -1 $x) != "$s"* ]] && sed -i -e "1d" out/$y
  #
  ## handle blank lines
  ${PYTHON3} -u ${top_dir}/format_xml.py $x out/${y}
  #
  ## convert from hex to decimal
  sed -i -e 's,\&#x2122,\&#8482,g'  out/$y
  sed -i -e 's,\&#xAE,\&#174,g'     out/$y
  sed -i -e 's,\&#xB1,\&#177,g'     out/$y
  #
  # fix issues # TODO
  ####[[ $y = mtb-bsp-manifest-fv2.xml ]] && sed -i -e 's,\&lt;div class="category",\&lt;div class=\&quot;category\&quot;,g'  out/$y
  ####[[ $y = mtb-ce-manifest-fv2.xml ]] && unix2dos out/$y
  ## diff the original and the generated file
  lines=$(diff $x out/$y | wc -l)
  if [[ ${lines} -ne 0 ]]; then
    echo ""
    echo "xmllint returned: ${rc}"
    echo "FATAL ERROR: formatting error:"
    ####diff --ignore-space-change $x out/$y || : # TODO
    diff $x out/$y || :
    g_failed=1
    echo ""
    echo "Manifest: ${manifest_file}"
    echo "failed format validation"
    echo ""
  else
    echo ""
    echo "Manifest: ${manifest_file}"
    echo "passed format validation"
    echo ""
  fi
  [[ ${rc} -ne 0 ]] && g_failed=1
  echo -e "####################"
}

function test_schema()
{
  echo -e "\n\n########## test schema ##########"
  requires_python3
  requires_python3_module lxml
  echo -e "+ detect_type g_manifest_type ${manifest_file}"
             detect_type g_manifest_type ${manifest_file}

  if [[ ! -z ${g_manifest_type} ]]; then
    set +e
    echo -e "+ ${PYTHON3} -u ${top_dir}/validate_schema.py ${g_manifest_type} ${manifest_file}"
               ${PYTHON3} -u ${top_dir}/validate_schema.py ${g_manifest_type} ${manifest_file}
    rc=$?
    ${restore_errexit}
    echo ""
    [[ ${rc} -ne 0 ]] && { echo "FATAL ERROR: '${manifest_file}' failed schema validation!"; g_failed=1; }
    echo -e "+ validate_category ${g_manifest_type} ${manifest_file}"
               validate_category ${g_manifest_type} ${manifest_file}
  else
    g_failed=1
  fi
  echo -e "####################"
}

function test_assets()
{
  echo -e "\n\n########## test assets ##########"
  requires_python3
  requires_python3_module lxml
  requires_python3_module requests
  echo -e "+ detect_type g_manifest_type ${manifest_file}"
             detect_type g_manifest_type ${manifest_file}

  if [[ ! -z ${g_manifest_type} ]]; then
    x=${manifest_file}
    y=${x##*/}
    rm -rf   out/${y}
    mkdir -p out
    set +e
    echo -e "+ ${PYTHON3} -u ${top_dir}/validate_assets.py ${g_manifest_type} ${x} out/${y}"
               ${PYTHON3} -u ${top_dir}/validate_assets.py ${g_manifest_type} ${x} out/${y}
    rc=$?
    ${restore_errexit}
    echo ""
    if [[ ${rc} -ne 0 ]]; then
      echo "FATAL ERROR: '${x}' failed processing!"
      g_failed=1
      echo ""
      echo "Manifest: ${manifest_file}"
      echo "Failed asset validation"
      echo ""
    else
      echo ""
      echo "Manifest: ${manifest_file}"
      echo "passed asset validation"
      echo ""
    fi
  else
    g_failed=1
  fi
  echo -e "####################"
}

function test_syntax_json()
{
  echo -e "\n\n########## test syntax json ##########"
  requires_python3

  set +e
  echo -e "+ ${PYTHON3} -u ${top_dir}/validate_json.py --syntax ${json_file}"
             ${PYTHON3} -u ${top_dir}/validate_json.py --syntax ${json_file}
  rc=$?
  ${restore_errexit}
  echo ""
  if [[ ${rc} -eq 0 ]]; then
    echo ""
    echo "JSON file: ${json_file}"
    echo "passed syntax validation"
    echo ""
  else
    echo "FATAL ERROR: '${json_file}' failed syntax validation!"
    g_failed=1
  fi
  echo -e "####################"
}

function test_format_json()
{
  echo -e "\n\n########## test format json ##########"
  requires_python3

  x=${json_file}
  y=${x##*/}
  rm -rf   out/${y}
  mkdir -p out

  set +e
  echo -e "+ ${PYTHON3} -u ${top_dir}/validate_json.py --format ${json_file} out/${y}"
             ${PYTHON3} -u ${top_dir}/validate_json.py --format ${json_file} out/${y}
  rc=$?
  ${restore_errexit}
  echo ""
  if [[ ${rc} -ne 0 ]]; then
    ## diff the original and the generated file
    echo -e "FATAL ERROR: formatting error(s)...\n"
    echo "+ diff ${json_file} out/${y}"
            diff ${json_file} out/${y} || :
    g_failed=1
    echo ""
    echo "JSON file: ${json_file}"
    echo "failed format validation"
    echo ""
  else
    echo ""
    echo "JSON file: ${json_file}"
    echo "passed format validation"
    echo ""
  fi
  echo -e "####################"
}

function test_rules()
{
  echo -e "\n\n########## test rules ##########"
  echo -e "####################"
}


## main

if [[ ${#manifest_files[@]} -eq 0 ]]; then
  # Process the 'super-manifest' file and detect all manifest files (and json files)
  ## prepend "ordering characters" ([1234],) so that "manifest_files" can be sorted;
  ##   need to process 'dependency' manifests last
  echo "[INFO] processing 'mtb-super-manifest' at: ${uri_super_manifest}"
  url_insteadof=${URL_INSTEADOF:-}
  if [[ -n ${url_insteadof} ]]; then
    _src="${url_insteadof##*\.insteadOf }"
    _dst="${url_insteadof%%\.insteadOf *}"
    uri_super_manifest=$(echo ${uri_super_manifest} | sed -e "s,${_src},${_dst},")
    printf "URL TRACE: ${uri_super_manifest}\n"
  fi
  manifest_files+=("1,"${uri_super_manifest})
  rm -rf ${uri_super_manifest#https://github.com/}
  while read_xml; do
    case "${ENTITY}" in
      "uri")
        x="${CONTENT//[[:space:]]}"  # strip all whitespace
        manifest_files+=("2,"${x})
        rm -rf ${x#https://github.com/}
        ;;
      "board-manifest "*)
        # find optional "dependency-url"
        if [[ ${ENTITY} = *" dependency-url="* ]]; then
          x=$(echo "${ENTITY}" | sed -e "s,^.* dependency-url=\([^ ]*\).*$,\1,")
          y="${x//[[:space:]]}"        # strip all whitespace
          z=${y//\"}                   # strip all double-quote characters
          manifest_files+=("4,"${z})
          rm -rf ${z#https://github.com/}
        fi
        # find optional "capability-url"
        if [[ ${ENTITY} = *" capability-url="* ]]; then
          x=$(echo "${ENTITY}" | sed -e "s,^.* capability-url=\([^ ]*\).*$,\1,")
          y="${x//[[:space:]]}"        # strip all whitespace
          z=${y//\"}                   # strip all double-quote characters
          manifest_files+=("3,"${z})
          rm -rf ${z#https://github.com/}
        fi
        ;;
      "middleware-manifest dependency-url="*)
        x=$(echo "${ENTITY}" | sed -e "s,^.*middleware-manifest dependency-url=\(.*\)$,\1,")
        y="${x//[[:space:]]}"        # strip all whitespace
        z=${y//\"}                   # strip all double-quote characters
        manifest_files+=("3,"${z})
        rm -rf ${z#https://github.com/}
        ;;
      *)
        expected=0
        content=${CONTENT//[[:space:]]}  # strip all whitespace
        [[ "${ENTITY}" = ''                              &&  "${content}" = "" ]]  && expected=1
        [[ "${ENTITY}" = 'super-manifest'                &&  "${content}" = "" ]]  && expected=1
        [[ "${ENTITY}" = 'super-manifest version="2.0"'  &&  "${content}" = "" ]]  && expected=1
        [[ "${ENTITY}" = '/super-manifest'               &&  "${content}" = "" ]]  && expected=1
        [[ "${ENTITY}" = 'app-manifest'                  &&  "${content}" = "" ]]  && expected=1
        [[ "${ENTITY}" = '/app-manifest'                 &&  "${content}" = "" ]]  && expected=1
        [[ "${ENTITY}" = 'app-manifest-list'             &&  "${content}" = "" ]]  && expected=1
        [[ "${ENTITY}" = '/app-manifest-list'            &&  "${content}" = "" ]]  && expected=1
        [[ "${ENTITY}" = 'board-manifest'                &&  "${content}" = "" ]]  && expected=1
        [[ "${ENTITY}" = '/board-manifest'               &&  "${content}" = "" ]]  && expected=1
        [[ "${ENTITY}" = 'board-manifest-list'           &&  "${content}" = "" ]]  && expected=1
        [[ "${ENTITY}" = '/board-manifest-list'          &&  "${content}" = "" ]]  && expected=1
        [[ "${ENTITY}" = 'middleware-manifest'           &&  "${content}" = "" ]]  && expected=1
        [[ "${ENTITY}" = '/middleware-manifest'          &&  "${content}" = "" ]]  && expected=1
        [[ "${ENTITY}" = 'middleware-manifest-list'      &&  "${content}" = "" ]]  && expected=1
        [[ "${ENTITY}" = '/middleware-manifest-list'     &&  "${content}" = "" ]]  && expected=1
        [[ "${ENTITY}" = '/uri'                          &&  "${content}" = "" ]]  && expected=1
        if [[ ${expected} -eq 0 ]]; then
          echo "FATAL ERROR: unexpected data:"
          echo "    [${ENTITY}] => [${CONTENT}]"
          echo "  in super-manifest file: ${uri_super_manifest}"
	  echo ""
          g_failed=1
        fi
        ;;
    esac
  done < <(curl -s -S -L ${uri_super_manifest})

  if [[ ${g_failed} -ne 0 ]]; then
    echo "FATAL ERROR: cannot continue, processing the super-manifest file failed!"
    exit 5
  fi

  #
  ## when processing the "super-manifest" tree,
  ## ensure that the 'out/asset_cache.txt' file (for the dependency manifests)
  ## has been cleared (unless this is a "custom super-manifest")
  [[ ${f_custom} -eq 0 ]] && rm -f out/asset_cache.txt
  mkdir -p  out
else
  # Process the specified manifest files
  ## prepend "ordering characters" ([123],) so that "manifest_files" can be sorted;
  ##   need to process 'dependency' manifests last
  for (( i=0; i<${#manifest_files[@]}; i++ )); do
    detect_type g_manifest_type ${manifest_files[$i]}
    case "${g_manifest_type}" in
      "super")
        manifest_files[$i]="1,"${manifest_files[$i]}
        ;;
      "dependency")
        manifest_files[$i]="3,"${manifest_files[$i]}
        ;;
      *)
        manifest_files[$i]="2,"${manifest_files[$i]}
        ;;
    esac
  done
  #
  ## when processing a single manifest file,
  ## allow the 'out/asset_cache.txt' file (for the dependency manifests)
  ## from a previous run (or manually seeded) to be used
  mkdir -p  out
fi

# order the manifest files; need to process 'dependency' manifests last
manifest_files=($(for x in ${manifest_files[@]}; do echo $x; done | sort))

# process the manifest file(s)
url_insteadof=${URL_INSTEADOF:-}
for x in ${manifest_files[@]}; do
  ((++num_found))
  y=${x#?,}  # strip the ordering characters
  echo -e "\n\n### Process: ${y}"
  z=${y#https://github.com/}
  if [[ ! -e ${z} ]]; then
    mkdir -p ${z%/*}
    if [[ -n ${url_insteadof} ]]; then
      _src="${url_insteadof##*\.insteadOf }"
      _dst="${url_insteadof%%\.insteadOf *}"
      y=$(echo ${y} | sed -e "s,${_src},${_dst},")
      printf "URL TRACE: ${y}\n"
    fi
    set -x
    curl -s -S -L ${y} -o ${z}
    { ${restore_xtrace}; } 2>/dev/null
  fi
  if [[ ${z} = *".json" ]]; then
    json_file=${z}
    [[ ${f_flags} -eq 0 || ${f_syntax} -eq 1 ]] && test_syntax_json
    [[ ${f_flags} -eq 0 || ${f_format} -eq 1 ]] && test_format_json
  else
    manifest_file=${z}
    [[ ${f_flags} -eq 0 || ${f_syntax} -eq 1 ]] && test_syntax
    [[ ${f_flags} -eq 0 || ${f_format} -eq 1 ]] && test_format
    [[ ${f_flags} -eq 0 || ${f_schema} -eq 1 ]] && test_schema
    [[ ${f_flags} -eq 0 || ${f_assets} -eq 1 ]] && test_assets
  fi
  ## test_rules
done

#if [[ -f out/asset_cache.txt ]]; then
#  echo "+ cat -n out/asset_cache.txt"
#          cat -n out/asset_cache.txt
#fi

[[ ${num_found} -gt 1 ]] && echo -e "\n\n... processed ${num_found} manifest files"
[[ ${g_failed} -ne 0 ]] && { echo -e "\n\nFATAL ERROR: one or more tests failed!"; exit 6; }

echo -e "\nSUCCESS: all tests passed!"

exit 0

## EOF
