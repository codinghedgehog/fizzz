#!/usr/bin/python
#
# Fizzz - File Size Subdirectory Sorter (Fisss, or Fizzz)
#
# Usage: fizzz.py [ -n <number of directories to split into> ] [ -s <src dir> ] [ -d <dest dir> ] [ -p <dir name prefix> ] [ -debug ] [ -mv ] [ -cp ] [ -t ] [ -f ]
#
# (File Size Subdirectory Sorter - Fizzz/Fisss) - Small (and rather
# project-specific) utility that takes a list of files or files in a directory
# and moves them into a user-specified number of folders such that the total size
# of each folder is roughly the same.
#
# Parameters (all optional):
# -n = Number of directories to sort the files into.  Defaults to number of processors, if detectable.
# -debug = Debug flag for verbose reporting during processing.
# -s <src dir> = Specify the source directory containing the files to be sorted.  Default is current directory.
# -d <dest dir> = Specify the target directory containing the subdirecotries to be created.  Default is current directory.
# -p <dir name prefix> = Specify a prefix for the directories created (default is processor: processor1, processor2, etc.).
# -mv = Move the files into the subdirectories. Default is to copy the files.
# -t = Test.  Just report the sorting results but DON'T actually create any directories or move any files.
# -f = Force.  By default fizzz will abort if the destination directory already exists.  This flag will ignore it.
# 
#

import sys
import os
import re
import argparse
import string
import cStringIO
import math
import multiprocessing
import shutil

VERSION = '1.0.0'

# CLASSES #

class FizzzDir:
    """Fizzz's representation of a target subdirectory for use during file sort calculations."""

    def __init__(self,name,targetdir=os.getcwd()):
        self.name = name 
        self.contents = {}
        self.fullPath=targetdir + "/" + self.name

    def __str__(self):
        strValue = "Name: {0}\nFull Path: {1}\nTotal Size: {2}".format(self.name,self.fullPath,self.totalSize())
        strValue += "\n" + str(self.contents)
        return strValue

    def assignFile(self,fileItem):
        """
        Assigns a file for this FizzzDir object to track.
        FileItem is a tuple or array of format (name/path, byte size).
        """
        self.contents[fileItem[0]] = numeric(fileItem[1])

    def totalSize(self):
        """Returns the current total size of assigned files."""
        return sum(self.contents.values())

    def numFiles(self):
        """Returns the current total number of assigned files."""
        return len(self.contents)

    def files(self):
        """Returns a list of the file names currently assigned to this dir object."""
        return self.contents.keys()

    def fileListing(self):
        """Returns the file list dictionary."""
        return self.contents

    def realize(self,move=False):
        """Actually copy (default) or move the assigned files into this directory, creating it if need be."""
        if not os.path.exists(self.fullPath):
            os.mkdir(self.fullPath)

        for fileItem in self.contents.items():
            filename = fileItem[0]
            if debugMode: print "Transporting {0} to {1}".format(filename,self.fullPath)
            if move:
                shutil.move(filename,self.fullPath)
            else:
                shutil.copy2(filename,self.fullPath)

# FUNCTIONS #

def numeric(numstr):
    """Returns an int or float value represented by the input string, or ValueError if no conversion is possible."""
    value=None
    try:
        value = int(numstr)
    except ValueError:
        value = float(numstr)

    return value

def assignNextBestFile(fizzzDir,sortedFileList,goalSize):
    """Assigns a file item from sortedFileList that puts the total size of fizzzDir closest to goalSize"""

    # If the directory is already larger than the target size, don't add assign any more files to it.
    if fizzzDir.totalSize() >= goalSize:
        return

    bestItem = None
    minDiff = goalSize
    currentDirSize = fizzzDir.totalSize()
    for fileItem in sortedFileList:
        currentDiff = abs(goalSize - (currentDirSize + fileItem[1]))
        if currentDiff < minDiff:
            bestItem = fileItem
            minDiff = currentDiff

    if bestItem:
        fizzzDir.assignFile(bestItem)
        sortedFileList.remove(bestItem)



# MAIN #

print "\nFizzz v{0}\n".format(VERSION)
print "File Size Subdirectory Sorter\n\n"

# Define our parameters and parse with argparse module.
argParser = argparse.ArgumentParser()

progname = os.path.abspath(sys.argv[0])

# Define arguments.
argParser.add_argument("-n","--numdirs",default=multiprocessing.cpu_count(),help="The number of directories to create and split into.", type=int) 
argParser.add_argument("-debug","--debug",action="store_true",help="Verbose output for debugging")
argParser.add_argument("-s","--srcdir",default=".",help="Directory with the files to sort.  Default is all files in the current working directory")
argParser.add_argument("-d","--destdir",default=".",help="Base directory that will contain the subdirectories with the sorted files.  Default is the current working directory")
argParser.add_argument("-p","--prefix",default="processor",help="Prefix for the directory name.  Default is 'processor'.")
argParser.add_argument("-mv","--move",action="store_true",help="Move the files into the subdirectories while sorting.  Default is to copy the files.")
argParser.add_argument("-t","--test",action="store_true",help="Calculate file assignations, but do not make any actual changes to the filesystem.")
argParser.add_argument("-f","--force",action="store_true",help="Ignore/overwrite existing destination directories.")

args = argParser.parse_args()

# Set debug mode.
debugMode = args.debug

# Working variables.
srcDir = args.srcdir
destDir = args.destdir
numDirs = args.numdirs
dirPrefix = args.prefix
doMove = args.move
dryRun = args.test
forceTransfer = args.force

if debugMode:
    print "Argparse results: "
    print args
    
if (not os.path.exists(srcDir)):
    print "Source directory {0} does not exist!".format(srcDir)
    sys.exit(1)

if dryRun:
    print "*** THIS IS A TEST RUN ONLY: No changes to the file system will be made. ***\n"

print "Attempting to sort files in '{0}' into {1} subdirectories.".format(srcDir,numDirs)
print "Subdirectories will be named starting with '{0}'.".format(dirPrefix)
print "Subdirectories will be created under the target base dir '{0}'.".format(destDir)

print "\nReading source directory..."

fileDataHash = {}

if debugMode: print "Ignoring non-standard files matching .*{0}\.[^{1}]*$".format(re.escape(os.sep),re.escape(os.sep))

for eachFile in os.listdir(srcDir):
    eachFile = os.path.normpath(os.path.abspath(srcDir + "/" + eachFile))

    if os.path.isdir(eachFile):
        print "Skipping directory {0}".format(eachFile)
        continue

    if os.path.islink(eachFile):
        print "Skipping link {0}".format(eachFile)
        continue

    if re.match(".*{0}\.[^{1}]*$".format(re.escape(os.sep),re.escape(os.sep)),eachFile):
        print "Skipping non-standard file: {0}".format(eachFile)
        continue

    if os.path.samefile(os.path.abspath(progname),eachFile):
        print "Skipping myself: {0}".format(eachFile)
        continue

    if os.path.isfile(eachFile):
        fileDataHash[eachFile]=os.path.getsize(eachFile)

numFiles = len(fileDataHash)
print "\nNumber of files found: {0}".format(numFiles)

totalSize = sum(fileDataHash.values())

print "Total size: {0} bytes".format(totalSize)

if debugMode:
    print "Collected files and sizes:"
    for eachKey in fileDataHash.keys():
        print "{0}\t{1}".format(eachKey,fileDataHash[eachKey])

avgSize = totalSize / numDirs

if numFiles < numDirs:
    print "\n*** ERROR: There are fewer files than there are target directories.  No sorting can occur.\n"
    print "Rerun with -n equal to the number of files if you want one file in each directory."
    sys.exit(1)

print "Target size for each subdirectory: {0} bytes.".format(avgSize)

# The idea is to fill each subdirectory so that it is close to the average size of the files.
# A quick and hopefully good-enough algorithm is:
#   0. Sort the file array by size.
#   1. For each empty subdirectory, put in the next largest element from the file array.
#   2. For each subdirectory (after the 1st pass), if it is smaller than the average size, then
#      add the element from the array that has the smallest difference between it and the avg size. Repeat.


sortedFileList = sorted(fileDataHash.items(),key=lambda x: x[1])

# Generate representations of the subdirectories for sort calculations.
dirList=[]
for i in range(numDirs):
    newDir = FizzzDir("{0}{1}".format(dirPrefix,i),os.path.abspath(destDir))
    dirList.append(newDir)
    if os.path.exists(newDir.fullPath):
        if forceTransfer:
            print "*** Warning: Destination path already exists: " + newDir.fullPath
        else:
            print "\n*** FATAL ERROR: Destination path already exists: " + newDir.fullPath
            print "To ignore and write to this anyway, rerun with the --force option."
            sys.exit(1)


# Assign the initial file to each directory, starting with the largest file.
for fizzzDir in dirList:
    fizzzDir.assignFile(sortedFileList.pop())

# Fill the smallest directories first when assigning the rest of the files.
dirList.reverse()

# Fill out the directories that have size < avgSize.  Add files to each that minimizes the difference between
# their current size and avgSize.
while sortedFileList:
    for fizzzDir in dirList:
        assignNextBestFile(fizzzDir,sortedFileList,avgSize)

if debugMode:
    print "Final sort results:"
    for fizzzDir in dirList:
        print fizzzDir

if dryRun:
    print "\n*** Test results:\n"
    for fizzzDir in dirList:
        print "Name: " + fizzzDir.fullPath
        print "Number of files: {0}".format(fizzzDir.numFiles())
        print "Total Size: {0}".format(fizzzDir.totalSize())
        print ""
    sys.exit(0)
else:
    if doMove:
        print "Moving files..."
    else:
        print "Copying files..."

    for fizzzDir in dirList:
        fizzzDir.realize(doMove)

print "Done!"


