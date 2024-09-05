import os, sys, shutil
from typing import Union, Optional
from glob import glob
from pathlib import Path

from pathlib import Path
current_dir = Path(__file__).absolute().parent.as_posix()
sys.path.insert(0, f"{current_dir}")
os.chdir(current_dir)

from Dataset_Creator.Creating_Directories import create_directories
from Dataset_Creator.Convert_SRT_to_CSV import change_encoding, convert_srt_to_csv
from Dataset_Creator.Change_Sample_Rate import preprocess_audio
from Dataset_Creator.Split_Audio import split_files
from Dataset_Creator.Create_DS_CSV import create_DS_csv
from Dataset_Creator.Merge_CSV import merge_csv
from Dataset_Creator.Merge_Transcripts_and_Files import merge_transcripts_and_wav_files
from Dataset_Creator.Clean import clean_unwanted_characters
from Dataset_Creator.Create_Dataset_Loading_Script import Transcript_Writer


class Dataset_Creating:
    '''
    1. Convert SRT to CSV
    2. Reorgnize CSV content
    3. Split and downsample WAV
    '''
    def __init__(self,
        SRT_Dir: str,
        AudioSpeakersData_Path: str,
        WAV_SampleRate: Optional[Union[int, str]] = 22050,
        WAV_SampleWidth: Optional[Union[int, str]] = '32 (Float)',
        WAV_ToMono: bool = False,
        #WAV_Time_Limitation: float = 10.00,
        DataFormat: str = 'PATH|NAME|[LANG]TEXT[LANG]',
        Add_AuxiliaryData: bool = False,
        AuxiliaryData_Path: str = './AuxiliaryData/AuxiliaryData.txt',
        TrainRatio: float = 0.7,
        #ToStandaloneForm: bool = False,
        Output_Root: str = "./",
        Output_DirName: str = "",
        FileList_Name_Training: str = 'Train_FileList',
        FileList_Name_Validation: str = 'Val_FileList'
    ):
        self.SRT_Dir = SRT_Dir
        def Get_WAV_Paths_Input():
            WAV_Paths_Input = []
            if Path(AudioSpeakersData_Path).is_dir():
                for SubPath in glob(Path(AudioSpeakersData_Path).joinpath('**', '*.wav').__str__(), recursive = True):
                    Audio = Path(SubPath).as_posix()
                    WAV_Paths_Input.append(Audio)
            if Path(AudioSpeakersData_Path).is_file():
                with open(file = AudioSpeakersData_Path, mode = 'r', encoding = 'utf-8') as AudioSpeakersData:
                    AudioSpeakerLines = AudioSpeakersData.readlines()
                for AudioSpeakerLine in AudioSpeakerLines:
                    Audio = AudioSpeakerLine.split('|')[0]
                    WAV_Paths_Input.append(Audio)
            return WAV_Paths_Input
        self.WAV_Paths_Input = Get_WAV_Paths_Input()
        self.WAV_SampleRate = eval(WAV_SampleRate) if WAV_SampleRate is not None else None
        self.WAV_SampleWidth = str(WAV_SampleWidth) if WAV_SampleWidth is not None else None
        self.WAV_ToMono = WAV_ToMono
        self.WAV_Dir_Split = Path(Output_Root).joinpath(Output_DirName).as_posix()
        def Get_AudioSpeakers():
            AudioSpeakers = {}
            if Path(AudioSpeakersData_Path).is_dir():
                for SubPath in glob(Path(AudioSpeakersData_Path).joinpath('**', '*.wav').__str__(), recursive = True):
                    Audio = Path(self.WAV_Dir_Split).joinpath(Path(SubPath).name).as_posix()
                    Speaker = Path(SubPath).parent.name
                    AudioSpeakers[Audio] = Speaker
            if Path(AudioSpeakersData_Path).is_file():
                with open(file = AudioSpeakersData_Path, mode = 'r', encoding = 'utf-8') as AudioSpeakersData:
                    AudioSpeakerLines = AudioSpeakersData.readlines()
                for AudioSpeakerLine in AudioSpeakerLines:
                    Audio = Path(self.WAV_Dir_Split).joinpath(Path(AudioSpeakerLine.split('|')[0]).name).as_posix()
                    Speaker = AudioSpeakerLine.split('|')[1].strip()
                    AudioSpeakers[Audio] = Speaker
            return AudioSpeakers
        self.AudioSpeakers = Get_AudioSpeakers()
        #self.WAV_Time_Limitation = WAV_Time_Limitation
        self.DataFormat = DataFormat.replace('路径', 'PATH').replace('人名', 'NAME').replace('语言', 'LANG').replace('文本', 'TEXT')
        self.AuxiliaryData_Path = AuxiliaryData_Path if Add_AuxiliaryData else None
        self.TrainRatio = TrainRatio
        self.ToStandaloneForm = True #self.ToStandaloneForm = ToStandaloneForm
        self.FileList_Path_Training = Path(self.WAV_Dir_Split).joinpath(FileList_Name_Training).as_posix() + ".txt"
        self.FileList_Path_Validation = Path(self.WAV_Dir_Split).joinpath(FileList_Name_Validation).as_posix() + ".txt"

    def CallingFunctions(self):
        SRT_Counter = len(glob(os.path.join(self.SRT_Dir, '*.srt')))

        if SRT_Counter == 0:
            print('!!! Please add srt_file(s) to %s-folder' %self.SRT_Dir)
            sys.exit()

        # Create directories
        WAV_Dir_Prepared = './Temp/ready_for_splitting'
        CSV_Dir_Prepared = './Temp/ready_for_merging'
        CSV_Dir_Merged = './Temp/merged_csv'
        CSV_Dir_Final = './Temp/final_csv'
        create_directories(WAV_Dir_Prepared, self.WAV_Dir_Split, CSV_Dir_Prepared, CSV_Dir_Merged, CSV_Dir_Final)

        # Changing encoding from utf-8 to utf-8-sig
        print('Encoding srt_file(s) to utf-8...')
        for SRT in glob(os.path.join(self.SRT_Dir, '*.srt')):
            change_encoding(SRT)
        print('Encoding of %s-file(s) changed' %SRT_Counter)
        print('---------------------------------------------------------------------')

        # Extracting information from srt-files to csv
        print('Extracting information from srt_file(s) to csv_files')
        for File in glob(os.path.join(self.SRT_Dir, '*.srt')):
            convert_srt_to_csv(File, CSV_Dir_Prepared)
        print('%s-file(s) converted and saved as csv-files to ./csv' %SRT_Counter)
        print('---------------------------------------------------------------------')

        # Pre-process audio for folder in which wav files are stored
        preprocess_audio(self.WAV_Paths_Input, self.WAV_SampleRate, self.WAV_SampleWidth, self.WAV_ToMono, WAV_Dir_Prepared)
        print('Pre-processing of audio files is complete.')
        print('---------------------------------------------------------------------')

        # Now slice audio according to start- and end-times in csv
        print('Slicing audio according to start- and end-times of transcript_csvs...')
        split_files(CSV_Dir_Prepared, self.WAV_Paths_Input, self.WAV_Dir_Split)
        WAV_Counter = len(glob(os.path.join(self.WAV_Dir_Split, '*.wav')))
        print('Slicing complete. {} files in dir {}'.format(WAV_Counter, self.WAV_Dir_Split))
        print('---------------------------------------------------------------------')

        # Now create list of filepaths and -size of dir ./split_audio
        create_DS_csv(self.WAV_Dir_Split, CSV_Dir_Merged)
        print('DS_csv with Filepaths - and sizes created.')
        print('---------------------------------------------------------------------')

        # Now join all seperate csv files
        merge_csv(CSV_Dir_Prepared, CSV_Dir_Merged)
        print('Merged csv with all transcriptions created.')
        print('---------------------------------------------------------------------')

        # Merge the csv with transcriptions and the file-csv with paths and sizes
        CSV_Name_Final = 'DS_training_final.csv'
        merge_transcripts_and_wav_files(CSV_Dir_Merged, CSV_Dir_Final, CSV_Name_Final)
        print('Final DS csv generated.')
        print('---------------------------------------------------------------------')

        # Clean the data of unwanted characters and translate numbers from int to words
        CSV_Path_Final_Cleaned = clean_unwanted_characters(CSV_Dir_Final, CSV_Name_Final)
        print('Unwanted characters cleaned.')
        print('---------------------------------------------------------------------')

        # Write transcript to text-file for model training
        Transcript_Writer(self.AudioSpeakers, self.DataFormat, CSV_Path_Final_Cleaned, self.AuxiliaryData_Path, self.TrainRatio, self.ToStandaloneForm, self.WAV_Dir_Split, self.FileList_Path_Training, self.FileList_Path_Validation)
        print('Transcript written.')
        print('---------------------------------------------------------------------')

        # Now remove the created folders
        for folders in [WAV_Dir_Prepared, CSV_Dir_Prepared, CSV_Dir_Merged, CSV_Dir_Final]:
            shutil.rmtree(folders, ignore_errors = True)
        print('Temp files removed.')
        print('********************************************** FINISHED ************************************************')

        print(f'Final processed audio is in {self.WAV_Dir_Split}')