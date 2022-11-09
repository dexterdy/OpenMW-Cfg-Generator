from collections import defaultdict
from dataclasses import dataclass
import os
import sys
from typing import List


@dataclass
class path:
    path: str
    name: str


skipped: List[path] = []


def generate_cfg(modList: List[path], cfgFile: str, reference: str, referenceIsCfg: bool, newCfg: str):
    espRefLines = []
    dataRefLines = []
    bsaRefLines = []
    espList = []
    bsaList = []

    if reference != None and referenceIsCfg:
        with open(reference) as reader:
            lines = reader.readlines()
            espRefLines = [x.strip()
                           for x in lines if x.startswith("content=")]
            dataRefLines = [x.strip() for x in lines if x.startswith("data=")]
            bsaRefLines = [
                x.strip() for x in lines if x.startswith("fallback-archive=")]
    elif reference != None:
        with open(reference) as reader:
            lines = reader.readlines()
            espRefLines = [x.strip() for x in lines if x.endswith(".esp") or x.lower().endswith(
                ".esm") or x.lower().endswith(".omwaddon")]
            bsaRefLines = [x.strip() for x in lines if x.endswith(".bsa")]
            dataRefLines = [x.strip() for x in lines]

    for mod in modList:
        with os.scandir(mod.path) as entries:
            for entry in entries:
                if entry.name.lower().endswith(".esp") or entry.name.lower().endswith(".esm") or entry.name.lower().endswith(".omwaddon"):
                    espList.append(entry)
                if entry.name.lower().endswith(".bsa"):
                    bsaList.append(entry)

    cfgEspList = []
    cfgDataList = []
    cfgBsaList = []
    with open(cfgFile) as reader:
        lines = reader.readlines()
        cfgEspList = [x.removeprefix("content=")
                      for x in lines if x.startswith("content=")]
        cfgDataList = [x.removeprefix("data=")
                       for x in lines if x.startswith("data=")]
        cfgBsaList = [x.removeprefix("fallback-archive=")
                      for x in lines if x.startswith("fallback-archive=")]

    newBsaLines = generate_cfg_lines(
        cfgBsaList, bsaList, bsaRefLines, "fallback-archive=", False)
    newEspLines = generate_cfg_lines(
        cfgEspList, espList, espRefLines, "content=", False)
    newDataLines = generate_cfg_lines(
        cfgDataList, modList, dataRefLines, "data=", True)

    with open(newCfg, 'w') as writer:
        for entry in newBsaLines:
            writer.write(entry + '\n')

        for entry in newDataLines:
            writer.write(entry + '\n')

        for entry in newEspLines:
            writer.write(entry + '\n')

def generate_cfg_lines(cfgList: list, dataList: list[path], refLines: list, prefix: str, cfgIsPath: bool, thresh: float) -> List[str]:

def generate_cfg_lines(cfgList: list[str], dataList: list[path], refLines: list, prefix: str, cfgIsData: bool) -> List[str]:
    newLines = []
    toSort = defaultdict(list)
    atEnd = []

    if cfgIsData == False:
        def cfg_name(x: str): return x
        def cfg_string(x: str): return x
        def data_string(x: path): return x.name
    else:
        def cfg_name(x: str): return os.path.basename(x)
        def cfg_string(x: str): return x
        def data_string(x: path): return x.path

    for cfgData in cfgList:
        highest = (-1, 0)
        for i, refLine in enumerate(refLines):
            distance = custom_string_similarity(refLine, cfg_name(cfgData))
            if distance > highest[1]:
                highest = (i, distance)
        if highest[0] < 0:
            atEnd.append(cfg_string(cfgData))
        else:
            toSort[highest[0]].append(cfg_string(cfgData))

    for newData in dataList:
        highest = (-1, 0)
        for i, refLine in enumerate(refLines):
            distance = custom_string_similarity(refLine, newData.name)
            if distance > highest[1]:
                highest = (i, distance)
        if highest[0] < 0:
            atEnd.append(data_string(newData))
        else:
            toSort[highest[0]].append(data_string(newData))

    for i in range(len(refLines)):
        if i not in toSort:
            continue
        for newData in toSort[i]:
            if cfgIsData:
                newLines.append(prefix + "\"" + newData + "\"")
            else:
                newLines.append(prefix + data)

    for data in atEnd:
        if cfgIsData:
            newLines.append(prefix + "\"" + newData + "\"")
        else:
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


def give_options(originalDir: path, dirList: List[path], ignoreAbsentNumers: bool) -> List[path]:
    print("there are multiple options in", originalDir.name)
    print("Choose one or more from the following list of options\n")
    for i, entry in enumerate(dirList):
        fstTwoAreNumbers = entry.name.lower()[:2].isnumeric()
        if fstTwoAreNumbers:
            name = entry.name[2:]
            print(str(i) + " " + name + "\n")
        elif ignoreAbsentNumers:
            name = entry.name
            print(str(i) + " " + name + "\n")
        else:
            dirList.pop(i)

    selected = input()
    if selected.upper() == 'S':
        skipped.append(originalDir)
        return []
    indices = selected.split()
    return [dirList[int(j)] for j in indices]


def find_mod_options(dir: path) -> List[path]:
    dirList: List[path] = []

    with os.scandir(dir.path) as entries:
        for entry in entries:
            if entry.is_dir():
                dirList.append(entry)

    return dirList


def check_mod_options(dir: path) -> bool:
    oneOption = False
    moreThanTwoOptions = False

    with os.scandir(dir.path) as entries:
        for entry in entries:
            if entry.is_dir():
                fstTwoAreNumbers = entry.name.lower()[:2].isnumeric()
                moreThanTwoOptions = (
                    oneOption and fstTwoAreNumbers) or moreThanTwoOptions
                oneOption = oneOption or fstTwoAreNumbers

    return moreThanTwoOptions


def find_correct_mod_dir(dir: path) -> List[path]:
    dirList = []

    if check_correct_mod_dir(dir):
        dirList.append(dir)
    else:
        with os.scandir(dir.path) as entries:
            for entry in entries:
                if entry.is_dir():
                    resultDir = find_correct_mod_dir(entry)
                    dirList.extend(resultDir)

    return dirList


def check_correct_mod_dir(dir: path) -> bool:
    subDirContainsDataOrEsp = False
    espInCurrentDir = check_esp_in_dir(dir)
    dataInCurrentDir = check_data_in_dir(dir)

    with os.scandir(dir.path) as entries:
        for entry in entries:
            if entry.is_dir():
                subDirContainsDataOrEsp = subDirContainsDataOrEsp or subdir_contains_data_or_esp(
                    entry)

    return (espInCurrentDir or dataInCurrentDir) and not subDirContainsDataOrEsp


def subdir_contains_data_or_esp(dir: path) -> bool:
    espInCurrentDir = check_esp_in_dir(dir)
    dataInCurrentDir = check_data_in_dir(dir)

    if espInCurrentDir or dataInCurrentDir:
        return True

    with os.scandir(dir.path) as entries:
        for entry in entries:
            if entry.is_dir():
                if subdir_contains_data_or_esp(entry):
                    return True


def check_data_in_dir(dir: path) -> bool:
    dataInCurrentDir = False

    with os.scandir(dir.path) as entries:
        for entry in entries:
            if entry.is_dir():
                if entry.name.lower() == "textures" or entry.name.lower() == "meshes" or entry.name.lower() == "animations" or entry.name.lower() == "icons" or entry.name.lower() == "fonts":
                    dataInCurrentDir = True

    return dataInCurrentDir


def check_esp_in_dir(dir: path) -> bool:
    containsEsp = False

    with os.scandir(dir.path) as entries:
        for entry in entries:
            if entry.is_file:
                if entry.name.lower().endswith(".esp") or entry.name.lower().endswith(".esm") or entry.name.lower().endswith(".omwaddon") or entry.name.lower().endswith(".bsa"):
                    containsEsp = True

    return containsEsp


def handle_defective_mod_dir(dir: path) -> List[path]:
    modDirs = []

    correct_dir = find_correct_mod_dir(dir)

    if len(correct_dir) == 0:
        print(
            "\nSorry, I could not find a valid mod in the following directory: ", "\"" + dir.path + "\"\n")
        selection = input(
            "\n[R]e-evaluate after fixing it manually, [S]kip: ")
        print()

        if selection.upper() == 'R':
            modDirs.extend(find_mods(dir))
        else:
            skipped.append(dir)

    elif len(correct_dir) == 1:
        newPath = path(correct_dir[0].path,
                       dir.name + "/" + correct_dir[0].name)
        modDirs.extend(find_mods(newPath))

    else:
        print("\ndirectory may contain mod, but is not formatted incorrectly:",
              "\"" + dir.path + "\"", "\n")
        selection = input(
            "\n[R]e-evaluate after fixing it manually, [C]hoose from list of possibly valid options, [S]kip: ")
        print()

        if selection.upper() == 'R':
            modDirs.extend(find_mods(dir))

        elif selection.upper() == 'C':
            selection = give_options(dir, correct_dir, True)
            for option in selection:
                newPath = path(option.path, dir.name + "/" + option.name)
                modDirs.extend(find_mods(newPath))

        else:
            skipped.append(dir)

    return modDirs

# pseudocode:
# for every subdirectory:
#   if it is a valid mod
#       install
#   if it is a mod with options
#       find all options
#       ask the user to select wanted options
#       for each selected option, go back to start of the loop using that options
#   it is not a valid mod nor a mod with options
#       if there is no valid option in the subdirectories, notify the user and skip
#       if there is only a single valid option in the subdirectories, go back to start of the loop using that directory
#       input: fix manually and come back, select from a list of valid options in subdirectories or skip
#       execute the selected option


def find_mods(dir: path) -> List[path]:
    print("\ninsalling mod in directory:", "\"" + dir.path + "\"", "\n")
    modDirs = []

    if check_correct_mod_dir(dir):
        modDirs.append(dir)
    elif check_mod_options(dir):
        options = find_mod_options(dir)
        options = give_options(dir, options, False)
        for option in options:
            newPath = path(option.path, dir.name + "/" + option.name)
            modDirs.extend(find_mods(newPath))
    else:
        modDirs.extend(handle_defective_mod_dir(dir))

    return modDirs


folder = sys.argv[1]
cfgFile = sys.argv[2]
reference = sys.argv[3]
newCfg = sys.argv[4]
flags = map(lambda x: x.lower(), sys.argv[4:])
referenceIsCfg = '-c' in flags
manyMods = '-m' in flags

modDirs = []

if manyMods:
    with os.scandir(folder) as entries:
        for entry in entries:
            if entry.is_dir():
                modDirs.extend(find_mods(entry))
else:
    modDirs = find_mods(path(folder, os.path.basename(folder)))

generate_cfg(modDirs, cfgFile, reference, referenceIsCfg, newCfg)

print("\nThe following directories were skipped during this installation. They might contain broken mods or not contain mods at all.\n")
for entry in skipped:
    print(entry.path)
