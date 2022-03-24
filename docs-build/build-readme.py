from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import argparse
import os


def readFileAsLines(filepath, trim=True):
    lines = []
    with open(filepath, 'r') as file:
        for line in file:
            cleanLine = line.strip() if trim else line.rstrip()
            if trim and cleanLine == "":
                continue
            lines.append(cleanLine)
    return lines


def grabAndCleanName(lines):
    key = ".. Title"
    if key not in lines:
        return None
    keyIndex = lines.index(key)
    nameIndex = keyIndex + 1
    if len(lines) <= nameIndex:
        return None
    return lines[nameIndex].split("--")[0].strip()


def grabAndCleanDescription(lines):
    startKey = ".. Description"
    endKey = ".. Aliases"
    if startKey not in lines or endKey not in lines:
        return ""
    startIndex = lines.index(startKey)
    endIndex = lines.index(endKey)
    if endIndex - startIndex <= 1:
        return ""
    description = ""
    for i in range(startIndex + 1, endIndex):
        if lines[i].strip(" .-") == "":
            continue
        descriptionLine = "{0}.".format(lines[i].strip(" .-"))
        description = "{0} {1}".format(description, descriptionLine)
    return description.strip()


def buildDocLink(urlBase, filepath):
    return "{0}{1}".format(urlBase, filepath)


def buildReadmeTable(content):
    table = ""
    header = "Name | Description\n--- | ---\n"
    table += header
    for item in content:
        table += "[{0}]({1})| {2}\n".format(item["name"],
                                            item["doclink"], item["description"])
    return table


def insertTableIntoReadme(readmePath, readmeTable):
    lines = readFileAsLines(readmePath, False)
    # just splice all entries before the before and after keys
    startKey = "<!--start collection content-->"
    endKey = "<!--end collection content-->"
    if startKey not in lines or endKey not in lines:
        return ""
    startIndex = lines.index(startKey)
    endIndex = lines.index(endKey)
    if startIndex >= endIndex:
        return
    start = lines[:startIndex + 1]
    end = lines[endIndex:]
    resultLines = start + [readmeTable.strip()] + end
    resultStr = "\n".join(resultLines)
    print(resultStr)
    a_file = open(readmePath, "w")
    a_file.write(resultStr)
    a_file.close()

    # then rebuild string with readmeTable in the middle
    # then write the file again
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs-dir", dest="docsDir",
                        type=str, help="Directory for docs")
    parser.add_argument("--url-base", dest="urlBase", type=str,
                        help="Base URL for building doc link")
    parser.add_argument("--readme-path", dest="readmePath",
                        type=str, help="Path to README")
    args = parser.parse_args()
    docsDir = args.docsDir
    urlBase = args.urlBase
    readmePath = args.readmePath
    content = []
    # tempRSTDir = os.path.join(os.path.dirname(os.path.realpath(__file__)),"temp-rst")
    for filename in os.listdir(docsDir):
        if not filename.endswith(".rst"):
            continue
        filepath = os.path.join(docsDir, filename)
        lines = readFileAsLines(filepath)
        name = grabAndCleanName(lines)
        if name is None:
            continue
        description = grabAndCleanDescription(lines)
        docLink = buildDocLink(urlBase, filepath)
        content.append({
            "name": name,
            "description": description,
            "doclink": docLink
        })
    readmeTable = buildReadmeTable(content)
    insertTableIntoReadme(readmePath, readmeTable)


if __name__ == "__main__":
    main()
