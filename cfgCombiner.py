import os
import sys

fileOne = sys.argv[1]
fileTwo = sys.argv[2]

fileOneLines = []
with open(fileOne) as reader:
    lines = reader.readlines()
    fileOneLines = [i.strip() for i in lines if i not in fileOneLines]

fileTwoLines = []
with open(fileTwo) as reader:
    lines = reader.readlines()
    fileTwoLines = [i.strip() for i in lines if i not in fileTwoLines]

if len(fileOneLines) >= len(fileTwoLines):
    large = fileOneLines
    small = fileTwoLines
else:
    large = fileTwoLines
    small = fileOneLines

for i, line in enumerate(small):
    if line in large:
        continue

    putAfterThisIndex = 0
    for x in range(i, 0, -1):
        if small[x] in large:
            putAfterThisIndex = large.index(small[x])
            break

    putBeforeThisIndex = len(large)
    for x in range(i, len(small), 1):
        if small[x] in large:
            putBeforeThisIndex = large.index(small[x])
            break

    if putBeforeThisIndex != len(large):
        large.insert(putBeforeThisIndex, line)
    elif putAfterThisIndex != 0:
        large.insert(putAfterThisIndex + 1, line)

with open(sys.argv[3],'w') as writer:
    for line in large:
        writer.write(line + '\n')
