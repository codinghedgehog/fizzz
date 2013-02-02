#!/usr/bin/python
#
# Fizzz - File Size Subdirectory Sorter (Fisss, or Fizzz)
#
# Usage: fizzz.py [ -n <number of directories to split into> ] [ -d <src dir> ] [ -p <dir name prefix> ] [ -debug ] [ -mv ] [ -cp ]
#
# (File Size Subdirectory Sorter - Fizzz/Fisss) - Small (and rather
# project-specific) utility that takes a list of files or files in a directory
# and moves them into a user-specified number of folders such that the total size
# of each folder is roughly the same. This script takes a BLAST result file and
# tabulates the number of top hits for each match across all the QUERYs in the
# file.
#
# Parameters (all optional):
# -n = Number of directories to sort the files into.  Defaults to number of processors, if detectable.
# -debug = Debug flag for verbose reporting during processing.
# -d <src dir> = Specify the source directory containing the files to be sorted.  Default is current directory.
# -p <dir name prefix> = Specify a prefix for the directories created (default is processor: processor1, processor2, etc.).
# -mv = Move the files into the subdirectories. Default is to copy the files.
#

import sys
import os
import re
import argparse
import string
import cStringIO
import math
import multiprocessing

VERSION = '1.0.0'


# FUNCTIONS #

def numeric(numstr):
    """Returns an int or float value represented by the input string, or ValueError if no conversion is possible."""
    value=None
    try:
        value = int(numstr)
    except ValueError:
        value = float(numstr)

    return value

# MAIN #

print "\nFizzz v{0}\n".format(VERSION)
print "File Size Subdirectory Sorter\n\n"

# Define our parameters and parse with argparse module.
argParser = argparse.ArgumentParser()

progname = sys.argv[0]

for afile in os.listdir("."):
    print afile 

# Define arguments.
argParser.add_argument("-n","--numdirs",default=multiprocessing.cpu_count(),help="The number of directories to create and split into.", type=int) 
argParser.add_argument("-debug","--debug",action="store_true",help="Verbose output for debugging")
argParser.add_argument("-d","--srcdir",default=".",help="Directory with the files to sort.  Default is all files in current directory")
argParser.add_argument("-p","--prefix",default="processor",help="Prefix for the directory name.  Default is 'processor'.")
argParser.add_argument("-mv","--move",action="store_true",help="Move the files into the subdirectories while sorting.  Default is to copy the files.")

args = argParser.parse_args()

# Set debug mode.
debugMode = args.debug

# Working variables.
srcDir = args.srcdir
numDirs = args.numdirs
dirPrefix = args.prefix
doMove = args.move

if args.debug:
    print "Argparse results: "
    print args
    
if (not os.path.exists(srcDir)):
    print "Source directory {0} does not exist!".format(srcDir)
    sys.exit(1)

