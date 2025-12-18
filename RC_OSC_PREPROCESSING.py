#####################################################################
#
#  RC OSC PREPROCESSING v1.0.0
#                                                                 
#  Script for Siril 1.4.0                                      
#                                                                   
#  December 2025
#
#  RC OSC PREPROCESSING
#
#  Author: Ron Claassen <claassen.ron@home.nl>
#
#  This script is provided without any guarantee.
#
################# RC OSC PREPROCESSING ##############################
#
#   THIS SCRIPT DOES NOT MOVE OR MAKES CHANGES
#   TO ANY OF THE SOURCE FILES
#
#   MULTI SESSION PREPROCESSING IS POSSIBLE
#
#   1. Choose Object folder.
#
#     Folder structure:
#     ../object_folder/session_folder1/flats/
#                     /session_folder1/lights/
#                     /session_folder2/flats/
#                     /session_folder2/lights/
#
#     Folder structure example:
#     ../NGC7380/2025-08-08/flats/
#           |.........|..../lights/
#           |.../2025-08-10/flats/
#           |........|...../lights/
#           |.../2025-08-12/flats/
#           |.../....|...../lights/
#
#   2. Choose folder for processing.
#       The script creates here a /process,
#       /masters and /all_lights folder.
#       If more then 2000 lights on Windows OS the script will
#       create batch folders of max 2000 files.
#
#   3. Choose bias files folder or master bias file.
#       If blank, preprocessing without master biase.
#
#   4. Choose dark files folder or master dark file.
#       If blank, preprocessing without master dark.
#
#   5. Option for setting the images bit dept for preprocessing.
#       Master stack always saved in 32 bit.
#   
#   6. Options for cleaning up processing folders.
#
#   7. Option for creating only a master bias file
#      and/or master dark file.
#
#   TODO:
#       Adding options
#       .........
#
#####################################################################

import sirilpy as s
s.ensure_installed("PyQt6")

import sys
import math
import shutil
from pathlib import Path
from sirilpy import LogColor

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QRadioButton,
    QCheckBox,
    QGroupBox,
    QFileDialog,
    QMessageBox,
)

TITLE = "RC OSC PREPROCESSING"
VERSION = "1.0.0"
AUTHOR = "Ron Claassen"

LIGHTS_COUNT = 2000 # MAX 2048 ON WINDOWS OS

flats_pattern = "flats"
lights_pattern= "lights"
session_flats_pattern = "flats_s*"
session_lights_pattern = "lights_s*"
pp_lights_pattern = "pp_light_s*.fit"
bias_cleanup_pattern = "*bias*"
darks_cleanup_pattern = "*dark*"
flats_cleanup_pattern = "*flat*"
lights_cleanup_pattern = "light_s*"
masters_pattern = "masters"
process_pattern = "process"
bias_master_pattern = "bias_master"
dark_master_pattern = "dark_master"
all_lights_pattern = "all_lights"
all_pp_lights_pattern = "all_pp_lights"
batch_pp_lights_pattern = "batch_pp_lights_"
batch_master_pattern = "batch_master"

def create_master_bias(self, bias_path_var, process_temp_path, masters_path):
    self.siril.cmd("cd", Path(bias_path_var))
    self.siril.cmd("convert", f"bias -out={process_temp_path}")
    self.siril.cmd("cd", process_temp_path)
    self.siril.cmd(
        "stack", f"bias rej 3 3 -nonorm -32b -out={masters_path}/{bias_master_pattern}"
    )
    self.siril.cmd("cd", masters_path)
    self.siril.log(f"FINISHED CREATING MASTER BIAS. ({masters_path}/{bias_master_pattern})", s.LogColor.GREEN)
        
def create_master_dark(self, dark_path_var, process_temp_path, masters_path):
    self.siril.cmd("cd", Path(dark_path_var))
    self.siril.cmd("convert", f"dark -out={process_temp_path}")
    self.siril.cmd("cd", process_temp_path)
    self.siril.cmd(
        "stack", f"dark rej 3 3 -nonorm -32b -out={masters_path}/{dark_master_pattern}"
    )
    self.siril.cmd("cd", masters_path)
    self.siril.log(f"FINISHED CREATING MASTER DARK. ({masters_path}/{dark_master_pattern})", s.LogColor.GREEN)
    
def create_master_flat(self, object_path_var, process_temp_path, bias_master, masters_path):
    object_array = Path(object_path_var).iterdir()                
    i = 1
    for object in object_array:
        self.siril.cmd("cd", f"{object}/{flats_pattern}")
        self.siril.cmd("convert", f"flat_s{i} -out={process_temp_path}")
        self.siril.cmd("cd", f"{process_temp_path}")
        if bias_master != "":
            self.siril.log(f"Calibrate with: Master Bias: {bias_master}", s.LogColor.GREEN)
            self.siril.cmd("calibrate", f"flat_s{i} -bias={bias_master}")
            self.siril.cmd("stack", f"pp_flat_s{i} rej 3 3 -norm=mul -32b -out={masters_path}/pp_flat_s{i}_stacked")
        else:
            self.siril.log(f"No Calibration (No Master Bias)", s.LogColor.GREEN)
            self.siril.cmd("stack", f"flat_s{i} rej 3 3 -norm=mul -32b -out={masters_path}/pp_flat_s{i}_stacked")  
        i += 1       
        self.siril.log("FINISHED CREATING MASTER FLATS.", s.LogColor.GREEN)

class RcPreprocessingInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.overwrite_checkbox_state = True
        
        self.setWindowTitle(f"{TITLE} - v{VERSION}")
        
        #self.setWindowFlag(Qt.WindowType.Tool, True)
        self.resize(1100, 550)
      
        self.siril = s.SirilInterface()
        try:
            self.siril.connect()
        except s.SirilConnectionError as e:
            self.siril.log(f"Connection failed: {e}", color=LogColor.RED)
            sys.exit()

        self.siril.log("Connected successfully!", color=LogColor.GREEN)

        if not self.initial_checks():
            self.close()
            sys.exit()
        
        self.initUI()
            
    def initial_checks(self):
        require_version = "1.4.0-beta3"
        try:
            self.siril.cmd("requires", require_version)
        except:
            self.siril.error_messagebox(
                f"This script requires Siril version {require_version} or later!"
            )
            return False
        
        return True
        
    def initUI(self):
        base_widget = QWidget()
        self.setCentralWidget(base_widget)
        
        layout = QVBoxLayout(base_widget)

        # 1 Title
        title_label = QLabel(f"{TITLE} - v{VERSION}")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 1 base_container_h
        #container_group = QGroupBox()
        container_layout = QHBoxLayout()
        #container_group.setLayout(container_layout)
        #layout.addWidget(container_group)
        layout.addLayout(container_layout)
        
        # 2 container_v
        #container_child_1_group = QGroupBox()
        container_child_1_layout = QVBoxLayout()
        #container_child_1_group.setLayout(container_child_1_layout)
        #container_layout.addWidget(container_child_1_group)
        container_layout.addLayout(container_child_1_layout)
        
        # Object group
        object_group = QGroupBox("Select Object Path")
        object_layout = QHBoxLayout()
        object_group.setLayout(object_layout)
        
        object_path_label = QLabel("Path:")
        object_path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        object_layout.addWidget(object_path_label)
        
        #self.object_path_var = QLineEdit("E:/TEST")
        self.object_path_var = QLineEdit()
        object_layout.addWidget(self.object_path_var)
        
        object_path_button = QPushButton("Browse")
        object_path_button.clicked.connect(self._object_browse_path)
        object_layout.addWidget(object_path_button)
        
        container_child_1_layout.addWidget(object_group)
        
        # Process group
        process_group = QGroupBox("Select Process Path")
        process_layout = QHBoxLayout()
        process_group.setLayout(process_layout)
        
        process_path_label = QLabel("Path:")
        process_path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        process_layout.addWidget(process_path_label)
        
        #self.process_path_var = QLineEdit("E:/TEST_WORK")
        self.process_path_var = QLineEdit()
        process_layout.addWidget(self.process_path_var)
        
        process_path_button = QPushButton("Browse")
        process_path_button.clicked.connect(self._process_browse_path)
        process_layout.addWidget(process_path_button)
        
        container_child_1_layout.addWidget(process_group)
        
        # Bias group
        bias_group = QGroupBox("Select Bias Path OR Master Dark File")
        bias_layout = QVBoxLayout()
        bias_group.setLayout(bias_layout)
        
        # Bias path group
        bias_path_group = QGroupBox()
        bias_path_layout = QHBoxLayout()
        bias_path_group.setLayout(bias_path_layout)
        
        bias_path_label = QLabel("Path:")
        bias_path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bias_path_layout.addWidget(bias_path_label)
        
        #self.bias_path_var = QLineEdit("E:/CALIBRATION_FRAMES/POSEIDON_C_PRO/BIASES_-10.00C_G125_O50")
        self.bias_path_var = QLineEdit()
        bias_path_layout.addWidget(self.bias_path_var)
        
        bias_path_button = QPushButton("Browse")
        bias_path_button.clicked.connect(self._bias_browse_path)
        bias_path_layout.addWidget(bias_path_button)
        
        bias_layout.addWidget(bias_path_group)
        
        # Bias file group
        bias_file_group = QGroupBox()
        bias_file_layout = QHBoxLayout()
        bias_file_group.setLayout(bias_file_layout)
        
        bias_file_label = QLabel("File:")
        bias_file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bias_file_layout.addWidget(bias_file_label)
        
        #self.bias_file_var = QLineEdit("E:/CALIBRATION_FRAMES/POSEIDON_C_PRO/MASTER_BIAS_50FR_-10.00C_G125_O50.fit")
        self.bias_file_var = QLineEdit()
        bias_file_layout.addWidget(self.bias_file_var)
        
        bias_file_button = QPushButton("Browse")
        bias_file_button.clicked.connect(self._bias_browse_file)
        bias_file_layout.addWidget(bias_file_button)
        
        bias_layout.addWidget(bias_file_group)
       
        container_child_1_layout.addWidget(bias_group)

        # Dark group
        dark_group = QGroupBox("Select Dark Path OR Master Dark File")
        dark_layout = QVBoxLayout()
        dark_group.setLayout(dark_layout)
        
        # Dark path group
        dark_path_group = QGroupBox()
        dark_path_layout = QHBoxLayout()
        dark_path_group.setLayout(dark_path_layout)
        
        dark_path_label = QLabel("Path:")
        dark_path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dark_path_layout.addWidget(dark_path_label)
        
        #self.dark_path_var = QLineEdit("E:/CALIBRATION_FRAMES/POSEIDON_C_PRO/DARKS_60s_-10.00C_G125_O50")
        self.dark_path_var = QLineEdit()
        dark_path_layout.addWidget(self.dark_path_var)
        
        dark_path_button = QPushButton("Browse")
        dark_path_button.clicked.connect(self._dark_browse_path)
        dark_path_layout.addWidget(dark_path_button)
        
        dark_layout.addWidget(dark_path_group)
        
        # Dark file group
        dark_file_group = QGroupBox()
        dark_file_layout = QHBoxLayout()
        dark_file_group.setLayout(dark_file_layout)
        
        dark_file_label = QLabel("File:")
        dark_file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dark_file_layout.addWidget(dark_file_label)
        
        #self.dark_file_var = QLineEdit("E:/CALIBRATION_FRAMES/POSEIDON_C_PRO/MASTER_DARK_50FR_60s_-10.00C_G125_O50.fit")
        self.dark_file_var = QLineEdit()
        dark_file_layout.addWidget(self.dark_file_var)
        
        dark_file_button = QPushButton("Browse")
        dark_file_button.clicked.connect(self._dark_browse_file)
        dark_file_layout.addWidget(dark_file_button)
        
        dark_layout.addWidget(dark_file_group)
        
        container_child_1_layout.addWidget(dark_group)
        
        # 2 container_v
        #container_child_2_group = QGroupBox()
        container_child_2_layout = QVBoxLayout()
        #container_child_2_group.setLayout(container_child_2_layout)
        #container_layout.addWidget(container_child_2_group)
        container_layout.addLayout(container_child_2_layout)
        
        # Clean up preprocessing
        bit_dept_group = QGroupBox("Choose bit dept images mode")
        bit_dept_layout = QVBoxLayout()
        bit_dept_group.setLayout(bit_dept_layout)
        
        # Set bit dept
        self.bit_dept_32_var = QRadioButton("32 bit", self)
        self.bit_dept_32_var.setChecked(True)
        
        self.bit_dept_16_var = QRadioButton("16 bit", self)
        
        bit_dept_layout.addWidget(self.bit_dept_32_var)
        bit_dept_layout.addWidget(self.bit_dept_16_var)
        
        container_child_2_layout.addWidget(bit_dept_group)
        
        # Clean up preprocessing
        cleanup_group = QGroupBox("Cleanup during preprocessing")
        cleanup_layout = QVBoxLayout()
        cleanup_group.setLayout(cleanup_layout)
        
        # Checkbox cleanup bias process files
        self.bias_cleanup_var = QCheckBox("Cleanup bias process files", self)
        self.bias_cleanup_var.setChecked(False)
        
        # Checkbox cleanup dark process files
        self.darks_cleanup_var = QCheckBox("Cleanup dark process files", self)
        self.darks_cleanup_var.setChecked(False)
        
        self.flats_cleanup_var = QCheckBox("Cleanup flat process files", self)
        self.flats_cleanup_var.setChecked(False)
        
        self.lights_cleanup_var = QCheckBox("Cleanup light process files", self)
        self.lights_cleanup_var.setChecked(False)
        
        cleanup_layout.addWidget(self.bias_cleanup_var)
        cleanup_layout.addWidget(self.darks_cleanup_var)
        cleanup_layout.addWidget(self.flats_cleanup_var)
        cleanup_layout.addWidget(self.lights_cleanup_var)
        
        container_child_2_layout.addWidget(cleanup_group)
        
        # Clean up after preprocessing
        cleanup_after_group = QGroupBox("Cleanup after preprocessing")
        cleanup_after_layout = QVBoxLayout()
        cleanup_after_group.setLayout(cleanup_after_layout)
        
        # Checkbox cleanup process folder
        self.process_cleanup_var = QCheckBox("Cleanup process folder", self)
        self.process_cleanup_var.setChecked(True)
        
        # Checkbox cleanup all lights folder
        self.all_pp_lights_cleanup_var = QCheckBox("Cleanup all_pp_lights folder", self)
        self.all_pp_lights_cleanup_var.setChecked(True)
        
        cleanup_after_layout.addWidget(self.process_cleanup_var)
        cleanup_after_layout.addWidget(self.all_pp_lights_cleanup_var)
        
        container_child_2_layout.addWidget(cleanup_after_group)
        
         # Only Bias and Darks
        bias_darks_group = QGroupBox("Create Only Master Bias and/or Master Dark")
        bias_darks_layout = QVBoxLayout()
        bias_darks_group.setLayout(bias_darks_layout)
        
        # Checkbox create bias stack 
        self.create_bias_var = QCheckBox("Create Master Bias", self)
        self.create_bias_var.setChecked(False)
        
        # Checkbox create dark stack
        self.create_dark_var = QCheckBox("Create Master Dark", self)
        self.create_dark_var.setChecked(False)
        
        bias_darks_layout.addWidget(self.create_bias_var)
        bias_darks_layout.addWidget(self.create_dark_var)
        
        container_child_2_layout.addWidget(bias_darks_group)
        
        # 1 Buttons
        button_layout = QHBoxLayout()
        help_button = QPushButton("Help")
        help_button.clicked.connect(self.help_messagebox)
        button_layout.addWidget(help_button)

        button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.run_close)
        button_layout.addWidget(close_button)

        submit_button = QPushButton("Apply")
        submit_button.clicked.connect(self.run_apply)
        #submit_button.clicked.connect(self.run_test)
        button_layout.addWidget(submit_button)

        layout.addLayout(button_layout)
    
    def _object_browse_path(self):
        path_name = QFileDialog.getExistingDirectory(self, "Select object path")
        if path_name:
            self.object_path_var.setText(str(Path(path_name)))
    
    def _process_browse_path(self):
        path_name = QFileDialog.getExistingDirectory(self, "Select process path")
        if path_name:
            self.process_path_var.setText(str(Path(path_name)))
    
    def _bias_browse_path(self):
        path_name = QFileDialog.getExistingDirectory(self, "Select bias path")
        if path_name:
            self.bias_path_var.setText(str(Path(path_name)))
            
    def _bias_browse_file(self):
        file_name, ok = QFileDialog.getOpenFileName(self, "Select bias file")
        if file_name:
            self.bias_file_var.setText(str(Path(file_name)))
            
    def _dark_browse_path(self):
        path_name = QFileDialog.getExistingDirectory(self, "Select dark path")
        if path_name:
            self.dark_path_var.setText(str(Path(path_name)))
            
    def _dark_browse_file(self):
        file_name, ok = QFileDialog.getOpenFileName(self, "Select dark file")
        if file_name:
            self.dark_file_var.setText(str(Path(file_name)))      
            
    def help_messagebox(self):
        help_messagebox = (
            f"{TITLE}""    v"f"{VERSION}\n\n"
            f"Author: {AUTHOR}\n\n"
            "THIS SCRIPT DOES NOT MOVE OR MAKES CHANGES\n"
            "TO ANY OF THE SOURCE FILES\n\n"
            "1. Choose Object folder.\n\n"
            "    Folder structure:\n"
            "    ../object_folder/session_folder1/flats/\n"
            "                             /session_folder1/lights/\n"
            "                             /session_folder2/flats/\n"
            "                             /session_folder2/lights/\n\n"
            "2. Choose folder for processing.\n"
            "    The script creates here a /process, /masters\n"
            "    and /all_lights folder.\n"
            "    If more then 2000 lights on windows the script will\n"
            "    create batch folders of max 2000 files\n"
            "3. Choose bias files folder or master bias file.\n"
            "    If blank preprocessing without master bias.\n"
            "4. Choose dark files folder or master dark file.\n"
            "    If blank preprocessing without master dark.\n"
            "5. Option for setting the images bitdept for preprocessing.\n"
            "    Master stack always saved in 32 bit.\n"
            "6. Options for cleaning up processing folders.\n"
            "7. Option for creating only a master bias file\n"
            "    and/or master dark file.\n"
        )
        QMessageBox.information(self, "Help", help_messagebox)
        #self.siril.log(help_messagebox, LogColor.GREEN)
         
    def run_close(self):
        self.close()
    
    def run_test(self):
        process_path_var = self.process_path_var.text()
        object_path_var = self.object_path_var.text()
        bias_path_var = self.bias_path_var.text()
        create_bias_var = self.create_bias_var.isChecked()
        create_dark_var = self.create_dark_var.isChecked()
        bit_dept_16_var = self.bit_dept_16_var.isChecked()
        masters_path = Path(process_path_var).joinpath(masters_pattern)
        flats_path = Path(object_path_var).joinpath(flats_pattern)
        
    def run_apply(self):
        try:
            object_path_var = self.object_path_var.text()
            process_path_var = self.process_path_var.text()
            bias_path_var = self.bias_path_var.text()
            bias_file_var = self.bias_file_var.text()
            dark_path_var = self.dark_path_var.text()
            dark_file_var = self.dark_file_var.text()
            process_cleanup_var = self.process_cleanup_var.isChecked()
            all_pp_lights_cleanup_var = self.all_pp_lights_cleanup_var.isChecked()
            create_bias_var = self.create_bias_var.isChecked()
            create_dark_var = self.create_dark_var.isChecked()
            bias_cleanup_var = self.bias_cleanup_var.isChecked()
            darks_cleanup_var = self.darks_cleanup_var.isChecked()
            flats_cleanup_var = self.flats_cleanup_var.isChecked()
            lights_cleanup_var = self.lights_cleanup_var.isChecked()
            bit_dept_32_var = self.bit_dept_32_var.isChecked()

            if bit_dept_32_var == True:
                set_bit_dept = "set32bits"
            else:
                set_bit_dept = "set16bits"
            
            # Check if paths are selected
            if create_bias_var == True or create_dark_var == True:
                if (process_path_var in (None, "") or not Path(process_path_var).is_dir()) or (create_bias_var == True and bias_path_var in (None, "") or not Path(bias_path_var).is_dir()) or (create_dark_var == True and dark_path_var in (None, "") or not Path(dark_path_var).is_dir()):
                    if (process_path_var in (None, "") or not Path(process_path_var).is_dir()):
                        self.siril.log(
                            "Select process folder.",
                            s.LogColor.SALMON
                        )
                    if create_bias_var == True and bias_path_var in (None, "") or not Path(bias_path_var).is_dir():
                        self.siril.log(
                            "Select bias folder.",
                            s.LogColor.SALMON
                        )         
                    if create_dark_var == True and dark_path_var in (None, "") or not Path(dark_path_var).is_dir():
                        self.siril.log(
                            "Select darks folder.",
                            s.LogColor.SALMON
                        )
                else:
                    # Create paths
                    masters_path = Path(process_path_var).joinpath(masters_pattern)
                    masters_path.mkdir(exist_ok=True)
                    process_temp_path = Path(process_path_var).joinpath(process_pattern)
                    process_temp_path.mkdir(exist_ok=True)
                    
                    # Set bitdept
                    self.siril.cmd(f"{set_bit_dept}")
                    
                    if create_bias_var == True:
                        create_master_bias(self, bias_path_var, process_temp_path, masters_path)
                    if create_dark_var == True:
                        create_master_dark(self, dark_path_var, process_temp_path, masters_path)

                    self.siril.cmd("set32bits")
                    
                    if process_cleanup_var == True and (process_temp_path not in (None, "") or Path(process_temp_path).is_dir()):
                        shutil.rmtree(process_temp_path, ignore_errors=True)
                        self.siril.log(
                            "Successfully cleaned up '%s' folder" % process_temp_path,
                            s.LogColor.GREEN,
                        )
                        
            # Check if paths are selected           
            elif ((object_path_var in (None, "") or not Path(object_path_var).is_dir()) or (process_path_var in (None, "") or not Path(process_path_var).is_dir())) or (bias_path_var not in (None, "") and bias_file_var not in (None, "")) or (dark_path_var not in (None, "") and dark_file_var not in (None, "")) or (not Path(bias_file_var).exists() or not Path(dark_file_var).exists()):
                if object_path_var in (None, "") or not Path(object_path_var).is_dir():
                    self.siril.log(
                        "Select object folder.",
                        s.LogColor.SALMON
                    )
                if (process_path_var in (None, "") or not Path(process_path_var).is_dir()):
                    self.siril.log(
                        "Select process folder.",
                        s.LogColor.SALMON
                    )
                if bias_path_var not in (None, "") and bias_file_var not in (None, ""):
                    self.siril.log(
                        "Both selected! Select bias folder or master bias file or none.",
                        s.LogColor.SALMON
                    )
                if dark_path_var not in (None, "") and dark_file_var not in (None, ""):
                    self.siril.log(
                        "Both selected! Select dark folder or master dark file or none.",
                        s.LogColor.SALMON
                    )
                if not Path(bias_file_var).exists():
                        self.siril.log(
                        f"Master bias file does not exist. - {bias_file_var}",
                        s.LogColor.SALMON
                        )
                if not Path(dark_file_var).exists():
                        self.siril.log(
                        f"Master dark file does not exist. - {dark_file_var}",
                        s.LogColor.SALMON
                        )    
            else: 
                # Check if flats / lights path / files exists       
                for object in sorted(Path(object_path_var).glob("*")):
                    if not Path(object.joinpath(flats_pattern)).exists():
                        self.siril.log(f"No flats folder in: {Path(object)}",
                        s.LogColor.RED
                        )
                        break
                    if not any(Path(object.joinpath(flats_pattern)).iterdir()):
                        self.siril.log(f"File path empty: {Path(object.joinpath(flats_pattern))}",
                        s.LogColor.RED
                        )
                        break
                    if not Path(object.joinpath(lights_pattern)).exists():
                        self.siril.log(f"No lights folder in: {Path(object)}",
                        s.LogColor.RED
                        )
                        break
                    if not any(Path(object.joinpath(lights_pattern)).iterdir()):
                        self.siril.log(f"File path empty: {Path(object.joinpath(lights_pattern))}",
                        s.LogColor.RED
                        )
                        break
                else:
                    self.siril.log("START PREPROCESSING",
                    s.LogColor.GREEN
                    ) 

                    # Set bitdept
                    self.siril.cmd(f"{set_bit_dept}")
                    
                    # Create paths
                    masters_path = Path(process_path_var).joinpath(masters_pattern)
                    masters_path.mkdir(exist_ok=True)
                    process_temp_path = Path(process_path_var).joinpath(process_pattern)
                    process_temp_path.mkdir(exist_ok=True)

                    all_pp_lights_temp_path = Path(process_path_var).joinpath(all_pp_lights_pattern)
                    all_batch_pp_lights_temp_path = Path(all_pp_lights_temp_path).joinpath(batch_pp_lights_pattern)
                    batch_temp_path = masters_path.joinpath(batch_master_pattern)
                    
                    # Check for bias / dark
                    if Path(bias_file_var).is_file():
                        bias_master = Path(bias_file_var)
                        self.siril.log(
                        f"Use Master Bias - {bias_master}",
                        s.LogColor.SALMON
                        )
                    elif bias_path_var in (None, "") or not Path(bias_path_var).is_dir():
                        bias_master = ""
                        self.siril.log(
                        "No Master Bias",
                        s.LogColor.SALMON
                        )
                    else:
                        create_master_bias(self, bias_path_var, process_temp_path, masters_path)
                        bias_master = Path(masters_path).joinpath(bias_master_pattern)
                        
                        if bias_cleanup_var == True:
                            for path in Path(process_temp_path).rglob(bias_cleanup_pattern):
                                Path(path).unlink()
                                print(f"Deleting: {path}")


                    if Path(dark_file_var).is_file():
                        dark_master = Path(dark_file_var)
                        self.siril.log(
                        f"Use Master Dark. - {dark_master}",
                        s.LogColor.SALMON
                        )
                    elif dark_path_var in (None, "") or not Path(dark_path_var).is_dir():
                        dark_master = ""
                        self.siril.log(
                        "No Master Dark.",
                        s.LogColor.SALMON
                        )
                    else:
                        create_master_dark(self, dark_path_var, process_temp_path, masters_path)
                        dark_master = Path(masters_path).joinpath(dark_master_pattern)
                        
                        if darks_cleanup_var == True:
                            for path in Path(process_temp_path).rglob(darks_cleanup_pattern):
                                Path(path).unlink()
            
                    # Create flats stack
                    create_master_flat(self, object_path_var, process_temp_path, bias_master, masters_path)
                        
                    if flats_cleanup_var == True:
                        for path in Path(process_temp_path).rglob(flats_cleanup_pattern):
                            Path(path).unlink()
                            
                    # Preprocessing light frames                        
                    if bias_master == "" and dark_master == "":
                        self.siril.log(f"Calibrate with: Only Master Flat", s.LogColor.GREEN) 
                        lights_calibration = ""
                    elif bias_master != "":
                        self.siril.log(f"Calibrate with: Master Bias and Master Flat", s.LogColor.GREEN)
                        lights_calibration = f"-bias={bias_master}"
                    else:
                        self.siril.log(f"Calibrate with: Master Dark and Master Flat", s.LogColor.GREEN)
                        lights_calibration = f"-dark={dark_master}"
                      
                    object_array = Path(object_path_var).iterdir()  
                    i = 1
                    for object in object_array:        
                        self.siril.cmd("cd", f"{object.joinpath(lights_pattern)}")
                        self.siril.cmd("convert", f"light_s{i} -out={process_temp_path}")
                        self.siril.cmd("cd", f"{process_temp_path}")
                        self.siril.cmd("calibrate", f"light_s{i} {lights_calibration} -flat={masters_path}/pp_flat_s{i}_stacked -cfa -equalize_cfa -debayer")
                        i += 1
                        
                    if lights_cleanup_var == True:
                        for path in Path(process_temp_path).rglob(lights_cleanup_pattern):
                            Path(path).unlink()
                    
                    if Path(all_pp_lights_temp_path).exists():
                        shutil.rmtree(all_pp_lights_temp_path, ignore_errors=True)
                        
                    self.siril.log("Creating all_pp_lights folder.", s.LogColor.GREEN)
                    all_pp_lights_temp_path.mkdir(exist_ok=True)
                    
                    # Windows 2048 limit check
                    pp_lights_count = sum(
                        1 for x in Path(process_temp_path).glob(pp_lights_pattern) 
                            if x.is_file()
                        )
                    
                    windows_platform = sys.platform.startswith("win")
                    if pp_lights_count <= LIGHTS_COUNT or not windows_platform:
                        self.siril.log(f"Count is less then {LIGHTS_COUNT}", s.LogColor.GREEN)
                        self.siril.log(f"Total count is: {pp_lights_count} light frames", s.LogColor.GREEN)
                        
                        for path in process_temp_path.rglob(pp_lights_pattern):
                            shutil.move(path, all_pp_lights_temp_path)
                            
                        # self.siril.log(f"Moved '{path.parts[-1]}' to {all_pp_lights_temp_path}.", s.LogColor.GREEN)
                        
                        # CREATE MASTER STACK
                        self.siril.log("Creating master_stack", s.LogColor.GREEN)
                        
                        self.siril.cmd("cd", all_pp_lights_temp_path)
                        self.siril.cmd("convert", f"all_light -out={process_temp_path}")
                        self.siril.cmd("cd", process_temp_path)
                        self.siril.cmd("register", "all_light")
                        self.siril.cmd("stack", f"r_all_light rej 3 3 -norm=addscale -output_norm -rgb_equal -32b -out={masters_path}/$OBJECT:%s$_$STACKCNT:%d$x$EXPTIME:%d$sec_G$GAIN:%d$_O$OFFSET:%d$_T$CCD-TEMP:%d$°C_$DATE-OBS:dm12$")
                        
                        self.siril.cmd("cd", masters_path)
                        
                        self.siril.log("FINISHED OSC PREPROCESSING.", s.LogColor.GREEN)
                        
                        self.siril.cmd("set32bits")
                    else:
                        # Create batch folders
                        self.siril.log(f"Count is more then {LIGHTS_COUNT}", s.LogColor.GREEN)
                        self.siril.log(f"Total count is: {pp_lights_count} light frames", s.LogColor.GREEN)
                        
                        batches_count = math.ceil(pp_lights_count / LIGHTS_COUNT)
                        
                        self.siril.log(f"Creating {batches_count} batch folders", s.LogColor.GREEN)
                        
                        for i in range(batches_count):
                            batch_path = f"{all_batch_pp_lights_temp_path}{i+1}"
                            Path(batch_path).mkdir(exist_ok=True)
                        for i, path in enumerate(
                            Path(process_temp_path).rglob(pp_lights_pattern), start=0
                            ):
                            batch_index = i // LIGHTS_COUNT
                            batch_path = f"{all_batch_pp_lights_temp_path}{batch_index + 1}"
                            shutil.move(path, batch_path)
                            
                            # self.siril.log(f"Batch: {batch_dir}", s.LogColor.GREEN)
                        
                        # CREATE MASTER STACK       
                        self.siril.log("Creating master_stack", s.LogColor.GREEN)
                        
                        all_pp_lights_array = Path(all_pp_lights_temp_path).iterdir()
                        i = 1
                        for all_pp_lights in all_pp_lights_array:
                            self.siril.log(f"Batch: {all_pp_lights}", s.LogColor.GREEN)
                            self.siril.cmd("cd", all_pp_lights)
                            self.siril.cmd("convert", f"light_all_{i} -out={process_temp_path}")
                            self.siril.cmd("cd", process_temp_path)
                            self.siril.cmd("register", f"light_all_{i}")
                            self.siril.cmd("stack", f"r_light_all_{i} rej 3 3 -norm=addscale -output_norm -rgb_equal -32b -out={batch_temp_path}/batch_light_all_{i}")
                            i += 1
                            
                        self.siril.cmd("cd", batch_temp_path)
                        self.siril.cmd("convert", f"batch_light_all -out={process_temp_path}")
                        self.siril.cmd("cd", process_temp_path)
                        self.siril.cmd("register", f"batch_light_all")
                        self.siril.cmd("stack", f"r_batch_light_all rej 3 3 -norm=addscale -output_norm -rgb_equal -32b -out={masters_path}/$OBJECT:%s$_$STACKCNT:%d$x$EXPTIME:%d$sec_G$GAIN:%d$_O$OFFSET:%d$_T$CCD-TEMP:%d$°C_$DATE-OBS:dm12$")
                        
                        self.siril.cmd("cd", masters_path)
                        
                        self.siril.cmd("set32bits")
                        
                        self.siril.log("FINISHED OSC PREPROCESSING.", s.LogColor.GREEN)
                        
                    if all_pp_lights_cleanup_var == True:
                        shutil.rmtree(all_pp_lights_temp_path, ignore_errors=True)
                        self.siril.log(
                            "Successfully cleaned up '%s' folder" % all_pp_lights_temp_path,
                            s.LogColor.GREEN,
                        )    
                    
                    if process_cleanup_var == True:
                        shutil.rmtree(process_temp_path, ignore_errors=True)
                        self.siril.log(
                            "Successfully cleaned up '%s' folder" % process_temp_path,
                            s.LogColor.GREEN,
                        )
                        
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            #self.siril.error_messagebox("Error", str(e))
              
def main():
    app = QApplication(sys.argv)
    window = RcPreprocessingInterface()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
