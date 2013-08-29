#!/usr/bin/env python

# Copyright (C) 2013 John Szakmeister <john@szakmeister.net>
# All rights reserved.
#
# This software is licensed as described in the file LICENSE.txt, which
# you should have received as part of this distribution.

import sys
import os
import re


__version__ = '0.1.0-dev'


class ScriptError(Exception):
    pass


class Tag(object):
    def __init__(self, tagName, tagFile, tagAddress):
        self.tagName = tagName
        self.tagFile = tagFile
        self.tagAddress = tagAddress
        self.fields = []

    def addField(self, type, value=None):
        if type == 'kind':
            type = None
        self.fields.append((type, value or ""))

    def _formatFields(self):
        formattedFields = []
        for name, value in self.fields:
            if name:
                s = '%s:%s' % (name, value or "")
            else:
                s = str(value)
            formattedFields.append(s)
        return '\t'.join(formattedFields)

    def __str__(self):
        return '%s\t%s\t%s;"\t%s' % (
                self.tagName, self.tagFile, self.tagAddress,
                self._formatFields())

    def __cmp__(self, other):
        return cmp(str(self), str(other))

    @staticmethod
    def section(section):
        tagAddress = '/^%s$/' % section.name
        t = Tag(section.name, section.filename, tagAddress)
        t.addField('kind', 's')
        t.addField('line', section.lineNumber)

        parents = []
        p = section.parent
        while p is not None:
            parents.append(p.name)
            p = p.parent
        parents.reverse()

        if parents:
            t.addField('section', '|'.join(parents))

        return t


class Section(object):
    def __init__(self, level, name, lineNumber, filename, parent=None):
        self.level = level
        self.name = name
        self.lineNumber = lineNumber
        self.filename = filename
        self.parent = parent

    def __repr__(self):
        return '<Section %s %d %d>' % (self.name, self.level, self.lineNumber)


headingRe = re.compile(r'^[-=^"#*.]+$')


def findSections(filename, lines):
    sections = []
    headingOrder = {}
    orderSeen = 1
    previousSections = []

    for i, line in enumerate(lines):
        if headingRe.match(line):
            if line[0] not in headingOrder:
                headingOrder[line[0]] = orderSeen
                orderSeen += 1

            if i == 0:
                continue

            name = lines[i-1].strip()
            level = headingOrder[line[0]]
            previousSections = previousSections[:level-1]
            if previousSections:
                parent = previousSections[-1]
            else:
                parent = None
            lineNumber = i

            s = Section(level, name, lineNumber, filename, parent)
            previousSections.append(s)
            sections.append(s)

    return sections


def sectionsToTags(sections):
    tags = []

    for section in sections:
        tags.append(Tag.section(section))

    return tags


def genTagsFile(output, tags):
    tags = sorted(tags)

    output.write('!_TAG_FILE_FORMAT	2\n')
    output.write('!_TAG_FILE_SORTED	1\n')

    for t in tags:
        output.write(str(t))
        output.write('\n')


def main():
    from optparse import OptionParser

    parser = OptionParser(usage = "usage: %prog [options] file(s)",
                          version = __version__)
    parser.add_option(
            "-f", "--file", metavar = "FILE", dest = "tagfile",
            default = "tags",
            help = 'Write tags into FILE (default: "tags").  Use "-" to write '
                   'tags to stdout.')
    parser.add_option(
            "", "--sort", metavar="SORT", dest = "sort",
            default = "yes",
            help = 'Produce sorted output.')

    options, args = parser.parse_args()

    if options.tagfile == '-':
        output = sys.stdout
    else:
        output = open(options.tagfile, 'wb')

    for filename in args:
        f = open(filename, 'rb')
        sections = findSections(filename, f.readlines())

        genTagsFile(output, sectionsToTags(sections))


if __name__ == '__main__':
    try:
        main()
    except ScriptError as e:
        print >>sys.stderr, "ERROR: %s" % str(e)
        sys.exit(1)
