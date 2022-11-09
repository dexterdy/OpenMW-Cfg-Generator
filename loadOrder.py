from collections import defaultdict
from dataclasses import dataclass
import os
import sys
from typing import List


@dataclass
class path:
    path: str
    name: str


cfgFile = sys.argv[2]
reference = sys.argv[3]
newCfg = sys.argv[4]
flags = map(lambda x: x.lower(), sys.argv[4:])
referenceIsCfg = '-c' in flags


def generate_cfg(cfgFile: str, reference: str, referenceIsCfg: bool, newCfg: str):
    espRefLines = []
    dataRefLines = []
    bsaRefLines = []
    espLines = []
    bsaLines = []
    dataLines = []

    if reference != None and referenceIsCfg:
        with open(reference) as reader:
            lines = reader.readlines()
            espRefLines = [x.removeprefix("content=")
                           for x in lines if x.startswith("content=")]
            dataRefLines = [x.removeprefix("data=")
                            for x in lines if x.startswith("data=")]
            bsaRefLines = [
                x.removeprefix("fallback-archive") for x in lines if x.startswith("fallback-archive=")]
    elif reference != None:
        with open(reference) as reader:
            lines = reader.readlines()
            espRefLines = [x for x in lines if x.endswith(".esp") or x.lower().endswith(
                ".esm") or x.lower().endswith(".omwaddon")]
            bsaRefLines = [x for x in lines if x.endswith(".bsa")]
            dataRefLines = [
                x for x in lines if x not in espRefLines and x not in bsaRefLines]

    with open(cfgFile) as reader:
        lines = reader.readlines()
        espLines = [x.removeprefix("content=")
                    for x in lines if x.startswith("content=")]
        dataLines = [x.removeprefix("data=")
                     for x in lines if x.startswith("data=")]
        bsaLines = [
            x.removeprefix("fallback-archive=") for x in lines if x.startswith("fallback-archive=")]

    newBsaLines = generate_cfg_lines(
        bsaLines, bsaRefLines, "fallback-archive=", 1.0/3.0)
    newEspLines = generate_cfg_lines(
        espLines, espRefLines, "content=", 1.0/3.0)
    newDataLines = generate_cfg_lines(
        dataLines, dataRefLines, "data=", 1.0/4.0)

    with open(newCfg, 'w') as writer:
        for entry in newBsaLines:
            writer.write(entry + '\n')

        for entry in newEspLines:
            writer.write(entry + '\n')

        for entry in newDataLines:
            writer.write(entry + '\n')


def generate_cfg_lines(cfgList: list, refLines: list, prefix: str, thresh: float) -> List[str]:
    newLines = []
    toSort = defaultdict(list)
    atEnd = []

    def cfg_name(x: str): return os.path.normpath(x.removeprefix("\"").removesuffix(
        "\"")).removeprefix(os.path.dirname(os.path.dirname(os.path.dirname(x))))

    for cfgData in cfgList:
        highest = (-1, 0)
        for i, refLine in enumerate(refLines):
            distance = custom_string_similarity(refLine, cfg_name(cfgData))
            if distance > highest[1]:
                highest = (i, distance)
        if highest[1] < thresh:
            atEnd.append(cfgData)
        else:
            toSort[highest[0]].append(cfgData)

    for i in range(len(refLines)):
        if i not in toSort:
            continue
        for newData in toSort[i]:
            newLines.append(prefix + newData)

    for data in atEnd:
        newLines.append(prefix + data)

    return newLines


# horrible optimization. I wanted to parallelize, but python is a bitch
def custom_string_similarity(fst: str, snd: str) -> int:
    longest = (fst if len(fst) > len(snd) else snd).lower()
    shortest = (snd if longest == fst else fst).lower()

    max = 0
    for shift in range(-(len(shortest)-1), len(longest)):
        value = 0

        for index in range(len(longest)):
            sIndex = index - shift
            if sIndex < 0 or sIndex >= len(shortest):
                continue

            if longest[index] == shortest[sIndex]:
                value += 1

        max = value if value > max else max

    return float(max) / float(len(shortest))


generate_cfg(cfgFile, reference, referenceIsCfg, newCfg)
