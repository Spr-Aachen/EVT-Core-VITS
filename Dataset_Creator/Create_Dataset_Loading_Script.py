import os
import pandas as pd
import random
import re
import shutil
from pathlib import Path


def Transcript_Writer(
    AudioSpeakers,
    DataFormat,
    CSV_Path,
    AuxiliaryData_Path,
    TrainRatio,
    ToStandaloneForm,
    Audio_Dir,
    Text_Path_Training,
    Text_Path_Validation
):
    '''
    CSV to TXT
    '''
    CSV_Path_DataSet = Path(CSV_Path).parent.joinpath("Dataset.csv").__str__()
    pd.read_csv(CSV_Path)[['wav_filename', 'transcript']].to_csv(
        path_or_buf = CSV_Path_DataSet,
        header = None,
        index = None,
        mode = 'w',
        sep = '|'
    )
    #shutil.copy(CSV_Path_DataSet, CSV_Save_Path) if CSV_Save_Path is not None else None
    with open(file = CSV_Path_DataSet, mode = 'r', encoding = 'utf-8') as File_Old:
        DataLines = File_Old.readlines()

    LangList = []
    for Line in DataLines:
        Line_LanguageText = Line.split('|', maxsplit = 1)[1]
        Line_Lang = re.split(r'[\[\]]', Line_LanguageText)[1]
        LangList.append(Line_Lang) if Line_Lang not in LangList else None

    def UpdateDataLines(DataLines, Text_Path):
        for Index, Line in enumerate(DataLines):
            Line_Path = Line.split('|', maxsplit = 1)[0]
            Audio = Path(Line_Path.rsplit('_', maxsplit = 1)[0] + Path(Line_Path).suffix).as_posix()
            Line_Name = AudioSpeakers[Audio]
            Line_LanguageText = Line.split('|', maxsplit = 1)[1]
            Line_Lang = re.split(r'[\[\]]', Line_LanguageText)[1].strip()
            Line_Text = re.split(r'[\[\]]', Line_LanguageText)[2].strip()
            if ToStandaloneForm:
                if Path(Line_Path).parent.as_posix() != Path(Audio_Dir).as_posix():
                    Line_Path_Dst = Path(Audio_Dir).joinpath(Path(Line_Path).name)
                    shutil.copy(Line_Path, Audio_Dir) if not Path(Line_Path_Dst).exists() else None
                    Line_Path = Line_Path_Dst
                Line_Path = f"./{Path(Line_Path).relative_to(Path(Text_Path).parent).as_posix()}"
            Line = DataFormat.replace('PATH', Line_Path).replace('NAME', Line_Name).replace('LANG', Line_Lang).replace('TEXT', Line_Text) + '\n'
            DataLines[Index] = Line
        return DataLines

    def UpdateAuxiliaryDataLines(AuxiliaryDataLines, Text_Path):
        print("Writing AuxiliaryData paths...")
        AuxiliaryDataLines_New = []
        for AuxiliaryDataLine in AuxiliaryDataLines:
            Line_Path = AuxiliaryDataLine.split('|', maxsplit = 1)[0]
            Line_Path = Path(AuxiliaryData_Path).parent.joinpath(Line_Path).as_posix()
            Line_Name = AuxiliaryDataLine.split("|", maxsplit = 2)[1]
            Line_LanguageText = AuxiliaryDataLine.split("|", maxsplit = 2)[2]
            Line_Lang = re.split(r'[\[\]]', Line_LanguageText)[1].strip()
            if Line_Lang not in LangList:
                continue
            Line_Text = re.split(r'[\[\]]', Line_LanguageText)[2].strip()
            if ToStandaloneForm:
                if Path(Line_Path).parent.as_posix() != Path(Audio_Dir).as_posix():
                    Line_Path_Dst = Path(Audio_Dir).joinpath(Path(Line_Path).name)
                    shutil.copy(Line_Path, Audio_Dir) if not Path(Line_Path_Dst).exists() else None
                    Line_Path = Line_Path_Dst
                Line_Path = f"./{Path(Line_Path).relative_to(Path(Text_Path).parent).as_posix()}"
            AuxiliaryDataLine = DataFormat.replace('PATH', Line_Path).replace('NAME', Line_Name).replace('LANG', Line_Lang).replace('TEXT', Line_Text) + '\n'
            AuxiliaryDataLines_New.append(AuxiliaryDataLine)
        return AuxiliaryDataLines_New

    random.shuffle(DataLines)
    TrainSize = int(len(DataLines) * TrainRatio)
    DataLines_Train = DataLines[:TrainSize]
    DataLines_Val = DataLines[TrainSize:]
    DataLines_Train = UpdateDataLines(DataLines_Train, Text_Path_Training)
    DataLines_Val = UpdateDataLines(DataLines_Val, Text_Path_Validation)
    if AuxiliaryData_Path is not None:
        with open(file = AuxiliaryData_Path, mode = 'r', encoding = 'utf-8') as AuxiliaryData:
            AuxiliaryDataLines = AuxiliaryData.readlines()
        random.shuffle(AuxiliaryDataLines)
        TrainSize = int(len(AuxiliaryDataLines) * TrainRatio)
        AuxiliaryDataLines_Train = AuxiliaryDataLines[:TrainSize]
        AuxiliaryDataLines_Val = AuxiliaryDataLines[TrainSize:]
        AuxiliaryDataLines_Train = UpdateAuxiliaryDataLines(AuxiliaryDataLines_Train, Text_Path_Training)
        AuxiliaryDataLines_Val = UpdateAuxiliaryDataLines(AuxiliaryDataLines_Val, Text_Path_Validation)
        ReplicateTimes = len(AuxiliaryDataLines_Train) // len(DataLines_Train) if len(AuxiliaryDataLines_Train) > len(DataLines_Train) else 1
        DataLines_Train = DataLines_Train * ReplicateTimes + AuxiliaryDataLines_Train
        DataLines_Val = DataLines_Val * ReplicateTimes + AuxiliaryDataLines_Val

    random.shuffle(DataLines_Train)
    random.shuffle(DataLines_Val)

    if len(DataLines_Train) > len(DataLines_Val) > 0:
        print("Writing VITS dataset paths...")
        def WriteDataLines(Text_Path, Lines):
            os.makedirs(os.path.dirname(Text_Path), exist_ok = True)
            with open(file = Text_Path, mode = 'w', encoding = 'utf-8') as File_New:
                File_New.writelines(Lines)
        WriteDataLines(Text_Path_Training, DataLines_Train)
        WriteDataLines(Text_Path_Validation, DataLines_Val)

    else:
        raise Exception(f"Lack of data!")