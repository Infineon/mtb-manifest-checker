"""
# Copyright 2022-2024, Cypress Semiconductor Corporation (an Infineon company) or
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
"""

import argparse
import os
import re
import requests
import shutil
import stat
import subprocess
import sys
from contextlib import contextmanager
from lxml import etree

# Compile regular expression for git repository URI
# (https://github.com/Infineon)/(mtb-example-btsdk-empty)
# (1) baseurl: https://github.com/Infineon
# (2) reponame: mtb-example-btsdk-empty
# (3) optional suffix: .git
RE_GIT_REPO_URI = re.compile(r'^(.*)/([^./]+)(\.git)?$')

# Compile regular expression for raw GitHub URI
# ((https://github.com)/(Infineon)/(mtb-mw-manifest))/raw/(v2.X)/(mtb-mw-manifest.xml)
# (1) repo: https://github.com/Infineon/mtb-mw-manifest
# (2) server: https://github.com
# (3) namespace: Infineon
# (4) reponame: mtb-mw-manifest
# (5) ref: v2.X
# (6) filename: mtb-mw-manifest.xml
RE_GIT_RAW_URI = re.compile(r'^((.*)/([^/]+)/([^/]+))/raw/([^/]+)/(.+)$')

# This database holds a cache of asset id's and uri's
# Key: ID, value: URI
ASSET_CACHE = {}

# This database holds a cache of HTTP GET requests
# Key: HTTP URL, value: server response
HTTP_CACHE = {}

# This database holds a cache of "git ls-remote" lookups
# Key: git remote URL, value: output of "git ls-remote <URL>" command
LS_REMOTE_CACHE = {}


def exec(*cmdline):
    """Execute command line, parse stdout, suppress stderr
    :param cmdline: command line array (command + arguments)
    :return: the contents of the stdout of a process
    """
    print(" ".join(cmdline))
    return subprocess.check_output(list(cmdline)).decode('utf-8')


def http_check(url):
    """Check URL points to valid HTTP location
    :param url: HTTP URL
    :return True if the URL points to valid web resource, False otherwise
    For optimization purposes, the HTTP requests are cached in HTTP_CACHE
    """
    global HTTP_CACHE
    if not url in HTTP_CACHE:
        response = requests.get(url, allow_redirects=True)
        HTTP_CACHE[url] = response
    else:
        response = HTTP_CACHE.get(url)
    # Accept HTTP codes < 400: 200, 301 or 302 redirects
    if not response.ok:
        print("INFO: http response status: {}".format(response.status_code))
    else:
        print("INFO [{}]: '{}' is accessible".format(response.status_code, url))
    return response.ok


def git_reference_check(git_repo, git_ref):
    """Check if git_ref exists in the git_repo
         - first try "git ls-remote"
         - if not successful, try "git_bare_repo_check()"
    :param git_repo: git repository URL
    :param git_ref: git object reference (tag, branch, commit)
    :return lines from git ls-remote output that match the git_ref pattern, or
       the line from 'git_bare_repo_check()'
    For optimization purposes, the "git ls-remote" lookups are cached in LS_REMOTE_CACHE
    """

    global LS_REMOTE_CACHE

    # perform a "git ls-remote" command
    git_ls_remote_output = ""
    if not git_repo in LS_REMOTE_CACHE:
        try:
            print("++ ", end='')
            git_ls_remote_output = exec('git', 'ls-remote', git_repo)
        except:
            print("FATAL ERROR: cannot access '{}'".format(git_repo))
        if git_ls_remote_output:
            LS_REMOTE_CACHE[git_repo] = git_ls_remote_output
    else:
        print("++ git ls-remote {} [cached]".format(git_repo))
        git_ls_remote_output = LS_REMOTE_CACHE.get(git_repo)

    # process the output of the "git ls-remote" command
    output = ""
    if git_ls_remote_output:
        for line in git_ls_remote_output.splitlines():
            m = re.match(r'^.*{}$'.format(git_ref), line) # match 'git_ref' at end of line
            if m:
                m1 = re.match(r'^[0-9a-f]*\trefs/heads/{}$'.format(git_ref), line)
                if m1:
                    # matched "refs/heads"
                    output = line
                m2 = re.match(r'^[0-9a-f]*\trefs/tags/{}$'.format(git_ref), line)
                if m2:
                    # matched "refs/tags"
                    output = line
                m3 = re.match(r'^[0-9a-f]*\t{}$'.format(git_ref), line)
                if m3:
                    # matched a commit hash
                    output = line
        if output:
            # dump output to stdout
            print(output)
            return output

    # if not found, perform a check in the bare repo
    output = git_bare_repo_check(git_repo, git_ref)
    if output:
        # dump output to stdout
        print(output.rstrip())
    return output


def git_bare_repo_check(git_repo, git_ref):
    """Check if git_ref exists in the git_repo
    :param git_repo: git repository URL
    :param git_ref: git object reference (commit)
    :return a line if the git_ref is found, None otherwise
    For optimization purposes, add any 'git_ref' found in the bare repo to the LS_REMOTE_CACHE
    """

    global LS_REMOTE_CACHE

    # Parse the repository data
    git_repo_match = re.match(RE_GIT_REPO_URI, git_repo)
    if not git_repo_match:
        print("FATAL ERROR: unable to parse the Git repository URI: {}".format(git_repo))
        return None
    git_baseuri = git_repo_match.group(1)
    git_reponame = git_repo_match.group(2)

    ## prepare temp directory
    cwd = os.getcwd()
    tmp_dir = cwd + "/tmp/" + git_reponame
    if not os.path.exists(cwd + "/tmp"):
        os.mkdir(cwd + "/tmp")
    if os.path.isdir(tmp_dir):
        # ensure "o+w" so that this can be deleted
        for root, dirs, files in os.walk(tmp_dir):
            for d in dirs:
                mode=os.stat(os.path.join(root, d)).st_mode
                os.chmod(os.path.join(root, d), (mode | stat.S_IWUSR))
            for f in files:
                mode=os.stat(os.path.join(root, f)).st_mode
                os.chmod(os.path.join(root, f), (mode | stat.S_IWUSR))
        shutil.rmtree(tmp_dir)
    os.mkdir(tmp_dir)
    os.chdir(tmp_dir)

    ## clone the bare repo
    try:
        print("++ ", end='')
        output = exec('git', 'clone', '--no-progress', '--mirror', git_baseuri + "/" + git_reponame)
    except:
        print("FATAL ERROR: cannot clone '{}'".format(git_baseuri + "/" + git_reponame))
        print(output)
        return None

    ## test for git_ref in the bare repo
    os.chdir(git_reponame + ".git")
    try:
        print("++ ", end='')
        output = exec('git', 'cat-file', '-t', git_ref)
    except:
        print("FATAL ERROR: cannot find '{}' in bare repo".format(git_ref))
        print(output)
        return None

    os.chdir(cwd)
    if os.path.isdir(tmp_dir):
        # ensure "o+w" so that this can be deleted
        for root, dirs, files in os.walk(tmp_dir):
            for d in dirs:
                mode=os.stat(os.path.join(root, d)).st_mode
                os.chmod(os.path.join(root, d), (mode | stat.S_IWUSR))
            for f in files:
                mode=os.stat(os.path.join(root, f)).st_mode
                os.chmod(os.path.join(root, f), (mode | stat.S_IWUSR))
        shutil.rmtree(tmp_dir)

    # add this git_ref to the cache
    cached = LS_REMOTE_CACHE.get(git_repo)
    LS_REMOTE_CACHE[git_repo] = "{}{}\t{}\n".format(cached, git_ref, git_ref)

    return "found {} in the bare repo".format(git_ref)


@contextmanager
def process_manifest(input_manifest, output_manifest):
    # Create ElementTree object https://docs.python.org/3/library/xml.etree.elementtree.html
    manifest_tree = etree.ElementTree()
    # Parse the XML tree
    # remove_blank_text is needed to correctly indent sections
    # strip_cdata is needed to preserve CDATA sections in the BSP manifest
    manifest_element = manifest_tree.parse(input_manifest, parser=etree.XMLParser(
        remove_blank_text=True, strip_cdata=False, remove_comments=True))
    # Pass the manifest_element context to the caller
    yield manifest_element
    # Save the processed manifest to the output file
    manifest_tree.write(output_manifest, pretty_print=True)


def process_super_element(super_element):
    """Process single element of the super manifest
    1. Check that the <uri> exists
    2. Check that the (optional) <dependecy-url> exists
    :param super_element: XML element in the super manifest
    :ttreturn: True if element(s) point to an existing XML file(s), False otherwise
    """

    # get the <uri> element
    uri_element = super_element.find('uri')
    git_raw = uri_element.text

    print("\nValidate super manifest [<uri>]: {}".format(git_raw))

    # Check the URI is valid
    if not http_check(git_raw):
        print("FATAL ERROR: cannot access: {}".format(git_raw))
        return False

    # Parse the repository data from the raw URI
    git_raw_match = re.match(RE_GIT_RAW_URI, git_raw)
    if not git_raw_match:
        print("FATAL ERROR: unable to parse the Git raw URI: {}".format(git_raw))
        return False

    git_repo = git_raw_match.group(1)
    git_server = git_raw_match.group(2)
    git_namespace = git_raw_match.group(3)
    git_reponame = git_raw_match.group(4)
    git_ref = git_raw_match.group(5)
    git_filename = git_raw_match.group(6)

    if "/" in git_filename:
        print("FATAL ERROR: invalid 'ref' detected in the Git raw URI: {}".format(git_raw))
        return False # code_0229

    # check if the git_ref is valid (branch/tag/commit)
    response = git_reference_check(git_repo, git_ref)
    if not response:
        print("FATAL ERROR: {} reference doesn't exist at {}".format(git_ref, git_repo))
        return False

    # process (optional) dependency-url
    dep_url = super_element.get("dependency-url")
    if dep_url is not None:
        print("\nValidate super manifest [<dependency-url>]: {}".format(dep_url))

        # Check the URI is valid
        if not http_check(dep_url):
            print("FATAL ERROR: cannot access: {}".format(dep_url))
            return False

        git_raw_dep_match = re.match(RE_GIT_RAW_URI, dep_url)
        if not git_raw_dep_match:
            print("FATAL ERROR: unable to parse the Git raw URI: {}".format(dep_url))
            return False

        git_dep_repo = git_raw_dep_match.group(1)
        git_dep_server = git_raw_dep_match.group(2)
        git_dep_namespace = git_raw_dep_match.group(3)
        git_dep_reponame = git_raw_dep_match.group(4)
        git_dep_ref = git_raw_dep_match.group(5)
        git_dep_filename = git_raw_dep_match.group(6)

        if "/" in git_dep_filename:
            print("FATAL ERROR: invalid 'ref' detected in the Git dep URI: {}".format(git_raw))
            return False # code_0228

        # check if the git_dep_ref is valid (branch/tag/commit)
        response = git_reference_check(git_dep_repo, git_dep_ref)
        if not response:
            print("FATAL ERROR: {} reference doesn't exist at {}".format(git_dep_ref, git_dep_repo))
            return False

    return True


def process_element(xml_element, uri_element_name):
    """Process single element of the BSP/application/middleware manifest
    1. For each <version> block, ensure that the <commit> exists for the <uri>
    2. ( save <id> and <uri> for processing "dependency" manifests )
    :param xml_element: XML element in the BSP/application/middleware manifest
    :param uri_element_name: name of the URI element
    :return True on success, False otherwise
    """

    # get the <id> content
    asset_id = xml_element.find('id').text

    # get the <uri>/<board_uri> element
    uri_element = xml_element.find(uri_element_name)
    git_repo = uri_element.text

    print("\nValidate manifest [<id> <{}>]: {} {}".format(uri_element_name, asset_id, git_repo))
    # save data for "dependency" manifest processing
    global ASSET_CACHE
    ASSET_CACHE[asset_id] = git_repo

    # parse the repository data
    git_repo_match = re.match(RE_GIT_REPO_URI, git_repo)
    if not git_repo_match:
        print("FATAL ERROR: unable to parse the Git repository URI: {}".format(git_repo))
        return False
    git_baseuri = git_repo_match.group(1)
    git_reponame = git_repo_match.group(2)

    # get the <versions> element
    versions_element = xml_element.find('versions')

    if versions_element is not None:

        # iterate over <version> elements
        for version_element in versions_element.findall('version'):

            # process the <commit> content
            commit = version_element.find('commit').text
            # check if the depender_commit is valid (branch/tag/commit)
            response = git_reference_check(git_repo, commit)
            if not response:
                print("FATAL ERROR: {} reference doesn't exist at {}".format(commit, git_repo))
                return False

    return True


def process_super_manifest(input_manifest, output_manifest):
    """ Process the URIs in the super manifest
    :param input_manifest: path to the input XML super manifest file
    :param output_manifest: path to the output XML super manifest file
    :return True on success, False otherwise
    """

    with process_manifest(input_manifest, output_manifest) as manifest:
        # get the <board-manifest-list> element
        board_manifest_list = manifest.find('board-manifest-list')
        if board_manifest_list is not None:
            # iterate over <board-manifest> elements
            for board_manifest in board_manifest_list.findall('board-manifest'):
                if not process_super_element(board_manifest):
                    return False

        # get the <app-manifest-list> element
        app_manifest_list = manifest.find('app-manifest-list')
        if app_manifest_list is not None:
            # iterate over <app-manifest> elements
            for app_manifest in app_manifest_list.findall('app-manifest'):
                if not process_super_element(app_manifest):
                    return False

        # get the <middleware-manifest-list> element
        middleware_manifest_list = manifest.find('middleware-manifest-list')
        if middleware_manifest_list is not None:
            # iterate over <middleware-manifest> elements
            for middleware_manifest in middleware_manifest_list.findall('middleware-manifest'):
                if not process_super_element(middleware_manifest):
                    return False

    return True


def process_board_manifest(input_manifest, output_manifest):
    """ Process the URIs in the BSP manifest
    :param input_manifest: path to the input XML manifest file
    :param output_manifest: path to the output XML manifest file
    :return True on success, False otherwise
    """

    with process_manifest(input_manifest, output_manifest) as manifest:
        # iterate over <board> elements
        for board_manifest in manifest.findall('board'):
            if not process_element(board_manifest, 'board_uri'):
                return False

    return True


def process_app_manifest(input_manifest, output_manifest):
    """ Process the URIs in the application manifest
    :param input_manifest: path to the input XML manifest file
    :param output_manifest: path to the output XML manifest file
    :return True on success, False otherwise
    """

    with process_manifest(input_manifest, output_manifest) as manifest:
        # iterate over <app> elements
        for app_manifest in manifest.findall('app'):
            if not process_element(app_manifest, 'uri'):
                return False

    return True


def process_middleware_manifest(input_manifest, output_manifest):
    """ Process the URIs in the middleware manifest
    :param input_manifest: path to the input XML manifest file
    :param output_manifest: path to the output XML manifest file
    :return True on success, False otherwise
    """

    with process_manifest(input_manifest, output_manifest) as manifest:
        # iterate over <middleware> elements
        for middleware_manifest in manifest.findall('middleware'):
            if not process_element(middleware_manifest, 'uri'):
                return False

    return True


def process_dependency_manifest(input_manifest, output_manifest):
    """ Process the depender/dependee elements in the dependency manifest
    :param input_manifest: path to the input XML manifest file
    :param output_manifest: path to the output XML manifest file
    :return True on success, False otherwise
    """

    global ASSET_CACHE

    with process_manifest(input_manifest, output_manifest) as manifest:

        # iterate over <depender> elements
        for depender_element in manifest.findall('depender'):
            # get the <id> content
            depender_id = depender_element.find('id').text
            # get depender repo from the ASSET_CACHE created when processing the BSP/application/middleware manifests
            depender_repo = ASSET_CACHE.get(depender_id)
            print("\nValidate dependency manifest [<depender> <id>=(uri)]: {} {}".format(depender_id, depender_repo))

            # get the <versions> element
            versions_element = depender_element.find('versions')

            # iterate over <version> elements
            for version_element in versions_element.findall('version'):

                # process the <commit> content
                depender_commit = version_element.find('commit').text
                # check if the depender_commit is valid (branch/tag/commit)
                response = git_reference_check(depender_repo, depender_commit)
                if not response:
                    print("FATAL ERROR: {} reference doesn't exist at {}".format(depender_commit, depender_repo))
                    return False

                # get the <dependees> element
                dependees_element = version_element.find('dependees')

                # iterate over <dependee> elements
                for dependee_element in dependees_element.findall('dependee'):
                    # get the <id> content
                    dependee_id = dependee_element.find('id').text
                    # get dependee repo from the ASSET_CACHE created when processing the BSP/application/middleware manifests
                    dependee_repo = ASSET_CACHE.get(dependee_id)

                    print("\nValidate dependency manifest [<dependee> <id>=(uri)]: {} {}".format(dependee_id, dependee_repo))

                    if not dependee_repo:
                        print("FATAL ERROR: '{}' has not been processed yet; cannot determine its URL!".format(dependee_id))
                        print("   ... perhaps seed the 'out/asset_cache.txt' file ...")
                        return False

                    # process the <commit> content
                    dependee_commit = dependee_element.find('commit').text
                    # check if the dependee_commit is valid (branch/tag/commit)
                    response = git_reference_check(dependee_repo, dependee_commit)
                    if not response:
                        print("FATAL ERROR: {} reference doesn't exist at {}".format(dependee_commit, dependee_repo))
                        return False

    return True


def main():
    global ASSET_CACHE

    argParser = argparse.ArgumentParser()
    argParser.add_argument("manifest_type", help="Manifest type")
    argParser.add_argument("input_manifest", help="Path to the input manifest")
    argParser.add_argument("output_manifest", help="Path to the output manifest")

    # parse command-line arguments
    args = argParser.parse_args()
    manifest_type = args.manifest_type
    input_manifest = args.input_manifest
    output_manifest = args.output_manifest

    # Create output directory
    output_dir = os.path.dirname(output_manifest)
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # seed the ASSET CACHE
    if os.path.exists("out/asset_cache.txt"):
        with open("out/asset_cache.txt", 'r') as f:
            lines = f.readlines()
            for line in lines:
                ASSET_CACHE[line.split()[0]] = line.split()[1]

    # process the manifest
    if manifest_type == "super":
        if not process_super_manifest(input_manifest, output_manifest):
            print("FATAL ERROR: failed to process the super manifest {}".format(input_manifest))
            sys.exit(1)
    elif manifest_type == "board":
        if not process_board_manifest(input_manifest, output_manifest):
            print("FATAL ERROR: failed to process the board manifest {}".format(input_manifest))
            sys.exit(1)
    elif manifest_type == "app":
        if not process_app_manifest(input_manifest, output_manifest):
            print("FATAL ERROR: failed to process the app manifest {}".format(input_manifest))
            sys.exit(1)
    elif manifest_type == "middleware":
        if not process_middleware_manifest(input_manifest, output_manifest):
            print("FATAL ERROR: failed to process the middleware manifest {}".format(input_manifest))
            sys.exit(1)
    elif manifest_type == "dependency":
        if not process_dependency_manifest(input_manifest, output_manifest):
            print("FATAL ERROR: failed to process the dependency manifest {}".format(input_manifest))
            sys.exit(1)
    else:
        print("FATAL ERROR: unknown manifest type: {}".format(manifest_type))
        sys.exit(1)

    # save the ASSET CACHE
    with open("out/asset_cache.txt", 'w', newline='') as f:
        # override os.linesep; do not generate '\r'
        for key, value in ASSET_CACHE.items():
            f.write('%s %s\n' % (key, value))


if __name__ == '__main__':
    main()
