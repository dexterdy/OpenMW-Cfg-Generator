from collections import defaultdict
from dataclasses import dataclass
import os
import sys
from typing import List


@dataclass
class path:
    path: str
    name: str


def remove_multiple_chars(string: str, chars: str) -> str:
    newstring = ""
    for char in string:
        if char not in chars:
            newstring += char
    return newstring


def generate_cfg(cfgFile: str, reference: str, referenceIsCfg: bool, newCfg: str):
    espRefLines = []
    dataRefLines = []
    bsaRefLines = []
    espLines = []
    bsaLines = []
    dataLines = []

    if referenceIsCfg:
        with open(reference) as reader:
            lines = reader.readlines()
            espRefLines = [x for x in lines if x.startswith("content=")]
            dataRefLines = [x for x in lines if x.startswith("data=")]
            bsaRefLines = [
                x for x in lines if x.startswith("fallback-archive=")]

    else:
        with open(reference) as reader:
            lines = reader.readlines()
            espRefLines = [x for x in lines if x.strip().lower().endswith(".esp") or x.strip(
            ).lower().endswith(".esm") or x.strip().lower().endswith(".omwaddon")]
            bsaRefLines = [
                x for x in lines if x.strip().lower().endswith(".bsa")]
            dataRefLines = [
                x for x in lines if x not in espRefLines and x not in bsaRefLines]

    with open(cfgFile) as reader:
        lines = reader.readlines()
        espLines = [x for x in lines if x.startswith("content=")]
        dataLines = [x for x in lines if x.startswith("data=")]
        bsaLines = [x for x in lines if x.startswith("fallback-archive=")]

    newBsaLines = generate_cfg_lines(
        bsaLines, bsaRefLines, "fallback-archive=", False,  3.0/7.0)
    newEspLines = generate_cfg_lines(
        espLines, espRefLines, "content=", False, 3.0/7.0)
    newDataLines = generate_cfg_lines(
        dataLines, dataRefLines, "data=", True, 1.0/3.0)

    with open(newCfg, 'w') as writer:
        writer.writelines(newBsaLines)

        writer.writelines(newDataLines)

        writer.writelines(newEspLines)


# don't mind the  mess please
def generate_cfg_lines(cfgList: list, refLines: list, prefix: str, cfgIsPath: bool, thresh: float) -> List[str]:
    newLines = []
    toSort = defaultdict(list)
    atEnd = []

    if cfgIsPath:
        def compare_string(x: str):
            stripped = x.strip()
            lowerCase = stripped.lower()
            withoutPrefix = lowerCase.removeprefix("content=").removeprefix(
                "data=").removeprefix("fallback-archive=")
            withoutQuotes = withoutPrefix.removeprefix("\"").removesuffix("\"")
            normalizedPath = os.path.normpath(withoutQuotes)
            onlyLastTwoComponents = normalizedPath.removeprefix(
                os.path.dirname(os.path.dirname(normalizedPath)))
            withoutDelimenators = remove_multiple_chars(
                onlyLastTwoComponents, " _-.0123456789")
            return withoutDelimenators
    else:
        def compare_string(x: str):
            stripped = x.strip()
            lowerCase = stripped.lower()
            withoutPrefix = lowerCase.removeprefix("content=").removeprefix(
                "data=").removeprefix("fallback-archive=")
            withoutSuffix = withoutPrefix.removesuffix(
                ".esm").removesuffix(".esp").removesuffix(".omwaddon")
            withoutDelimenators = remove_multiple_chars(
                withoutSuffix, " _-.0123456789")
            return withoutDelimenators

    for cfgData in cfgList:
        highest = (-1, 0.0)
        cfgCompareString = compare_string(cfgData)

        for i, refLine in enumerate(refLines):

            similariy = custom_string_similarity(compare_string(refLine), cfgCompareString)
            if similariy > highest[1]:
                highest = (i, similariy)

        if highest[1] < thresh:
            atEnd.append(cfgData)
        else:
            print(compare_string(cfgData), compare_string(refLines[highest[0]]))
            toSort[highest[0]].append((cfgData, highest[1]))

    for i in range(len(refLines)):
        if i not in toSort:
            continue

        matches = toSort[i]
        matches.sort(key=lambda x: x[1], reverse=True)

        for entry in matches:
            newLines.append(entry[0])

    for data in atEnd:
        newLines.append(data)

    return newLines


# horrible optimization. I wanted to parallelize, but python is a bitch
def custom_string_similarity(fst: str, snd: str) -> float:
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


def main(arg1, arg2, arg3, arg4):
    cfgFile = arg1
    reference = arg2
    newCfg = arg3
    flags = map(lambda x: x.lower(), arg4)
    referenceIsCfg = '-c' in flags
    generate_cfg(cfgFile, reference, referenceIsCfg, newCfg)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[3:])
