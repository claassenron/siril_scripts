#####################################################################
#
#  RC OSC PREPROCESSING v1.0.0
#                                                                 
#  Script for Siril 1.4.2                                     
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
#     ../object_folder/session_folder1/flats/ (optional with No Flats)
#                     /session_folder1/lights/
#                     /session_folder2/biases/ (optional)
#                     /session_folder2/darks/ (optional)
#                     /session_folder2/flats/ (optional with No Flats)
#                     /session_folder2/lights/
#                     /session_folder2/biases/ (optional)
#                     /session_folder2/darks/ (optional)
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
#   3. Choose in session biases folder or choose separately a 
#       bias files folder or master bias file.
#       If blank, preprocessing without master bias.
#
#   4. Choose in session darks folder or choose separately a
#       dark files folder or master dark file.
#       If blank, preprocessing without master dark.
#
#   5. Option for preprocessing without flats.
#
#   6. Option for setting the images bit dept for preprocessing.
#       Master stack always saved in 32 bit.
#
#   7. Option for drizzle
#
#   8. Options for cleaning up processing folders.
#
#   9. Option for creating only a master bias file
#      and/or master dark file.
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
    QComboBox
)

TITLE = "RC OSC PREPROCESSING"
VERSION = "1.0.0"
AUTHOR = "Ron Claassen"

LIGHTS_COUNT = 2000 # MAX 2048 ON WINDOWS OS

DARK_THEME_STYLESHEET = """
QMainWindow,
QWidget {
    background-color: #15171c;
    color: #e6e8ee;
    font-size: 10pt;
}

QLabel {
    color: #d8dce6;
}

QLabel#titleLabel {
    color: #f4f6fb;
    font-size: 15pt;
    font-weight: 600;
    padding: 10px 0 14px 0;
}

QGroupBox {
    background-color: #1d2027;
    border: 1px solid #363b46;
    border-radius: 6px;
    margin-top: 14px;
    padding: 12px 10px 10px 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    color: #9db8ff;
    padding: 0 6px;
    left: 10px;
}

QLineEdit,
QComboBox {
    background-color: #101217;
    border: 1px solid #3a404c;
    border-radius: 4px;
    color: #f0f2f7;
    min-height: 26px;
    padding: 3px 8px;
    selection-background-color: #4268d6;
}

QLineEdit:focus,
QComboBox:focus {
    border-color: #6f8fff;
}

QComboBox::drop-down {
    border: 0;
    width: 24px;
}

QPushButton {
    background-color: #2a2f3a;
    border: 1px solid #424958;
    border-radius: 4px;
    color: #f4f6fb;
    min-height: 28px;
    min-width: 78px;
    padding: 4px 12px;
}

QPushButton:hover {
    background-color: #343a47;
    border-color: #5a6375;
}

QPushButton:pressed {
    background-color: #20242d;
}

QPushButton#applyButton {
    background-color: #3b63d7;
    border-color: #6788ee;
    font-weight: 600;
}

QPushButton#applyButton:hover {
    background-color: #456fe9;
}

QRadioButton,
QCheckBox {
    color: #e6e8ee;
    spacing: 8px;
    min-height: 22px;
}

QRadioButton::indicator,
QCheckBox::indicator {
    background-color: #101217;
    border: 1px solid #4c5362;
    height: 14px;
    width: 14px;
}

QRadioButton::indicator {
    border-radius: 8px;
}

QCheckBox::indicator {
    border-radius: 3px;
}

QRadioButton::indicator:checked,
QCheckBox::indicator:checked {
    background-color: #6f8fff;
    border-color: #9db8ff;
}

QMessageBox {
    background-color: #1d2027;
}
"""

biases_pattern = "biases"
darks_pattern = "darks"
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

def get_session_paths(object_path_var):
    return sorted(
        (path for path in Path(object_path_var).iterdir() if path.is_dir()),
        key=lambda path: path.name.lower()
    )

def folder_has_files(path):
    return path.is_dir() and any(child.is_file() for child in path.iterdir())

def validate_session_frame_folders(object_path_var, no_flats_var, bias_session_var, dark_session_var):
    warnings = []
    sessions = get_session_paths(object_path_var)
    if not sessions:
        return ["Object folder contains no session folders."]

    required_folders = [(lights_pattern, "lights")]
    if not no_flats_var:
        required_folders.append((flats_pattern, "flats"))
    if bias_session_var:
        required_folders.append((biases_pattern, "biases"))
    if dark_session_var:
        required_folders.append((darks_pattern, "darks"))

    for session_path in sessions:
        for folder_name, label in required_folders:
            frame_path = session_path.joinpath(folder_name)
            if not frame_path.is_dir():
                warnings.append(f"No {label} folder in: {session_path}")
            elif not folder_has_files(frame_path):
                warnings.append(f"{label.capitalize()} folder is empty: {frame_path}")

    return warnings

def create_master_bias(self, bias_path_var, process_temp_path, masters_path):
    self.siril.cmd("cd", Path(bias_path_var))
    self.siril.cmd("convert", f"bias -out={process_temp_path}")
    self.siril.cmd("cd", process_temp_path)
    self.siril.cmd(
        "stack", f"bias rej 3 3 -nonorm -32b -out={masters_path}/{bias_master_pattern}"
    )
    self.siril.cmd("cd", masters_path)
    self.siril.log(f"FINISHED CREATING MASTER BIAS. ({masters_path}/{bias_master_pattern})", s.LogColor.GREEN)

def create_session_master_bias(self, object_path_var, process_temp_path, masters_path):
    object_array = get_session_paths(object_path_var)
    bias_masters = []
    i = 1
    for object in object_array:
        bias_master = Path(masters_path).joinpath(f"{bias_master_pattern}_{i}")
        self.siril.cmd("cd", f"{object}/{biases_pattern}")
        self.siril.cmd("convert", f"bias_s{i} -out={process_temp_path}")
        self.siril.cmd("cd", process_temp_path)
        self.siril.cmd(
            "stack", f"bias_s{i} rej 3 3 -nonorm -32b -out={bias_master}"
        )
        self.siril.cmd("cd", masters_path)
        self.siril.log(f"FINISHED CREATING MASTER BIAS. ({bias_master})", s.LogColor.GREEN)
        bias_masters.append(bias_master)
        i += 1  
    return bias_masters
       
def create_master_dark(self, dark_path_var, process_temp_path, masters_path):
    self.siril.cmd("cd", Path(dark_path_var))
    self.siril.cmd("convert", f"dark -out={process_temp_path}")
    self.siril.cmd("cd", process_temp_path)
    self.siril.cmd(
        "stack", f"dark rej 3 3 -nonorm -32b -out={masters_path}/{dark_master_pattern}"
    )
    self.siril.cmd("cd", masters_path)
    self.siril.log(f"FINISHED CREATING MASTER DARK. ({masters_path}/{dark_master_pattern})", s.LogColor.GREEN)

def create_session_master_dark(self, object_path_var, process_temp_path, masters_path):
    object_array = get_session_paths(object_path_var)
    dark_masters = []
    i = 1
    for object in object_array:
        dark_master = Path(masters_path).joinpath(f"{dark_master_pattern}_{i}")
        self.siril.cmd("cd", f"{object}/{darks_pattern}")
        self.siril.cmd("convert", f"dark_s{i} -out={process_temp_path}")
        self.siril.cmd("cd", process_temp_path)
        self.siril.cmd(
            "stack", f"dark_s{i} rej 3 3 -nonorm -32b -out={dark_master}"
        )
        self.siril.cmd("cd", masters_path)
        self.siril.log(f"FINISHED CREATING MASTER DARK. ({dark_master})", s.LogColor.GREEN)
        dark_masters.append(dark_master)
        i += 1  
    return dark_masters
    
def create_master_flat(self, object_path_var, process_temp_path, bias_master, masters_path):
    object_array = get_session_paths(object_path_var)
    i = 1
    for object in object_array:
        session_bias_master = bias_master[i - 1] if isinstance(bias_master, list) else bias_master
        self.siril.cmd("cd", f"{object}/{flats_pattern}")
        self.siril.cmd("convert", f"flat_s{i} -out={process_temp_path}")
        self.siril.cmd("cd", f"{process_temp_path}")
        if session_bias_master != "":
            self.siril.log(f"Calibrate with: Master Bias: {session_bias_master}", s.LogColor.GREEN)
            self.siril.cmd("calibrate", f"flat_s{i} -bias={session_bias_master}")
            self.siril.cmd("stack", f"pp_flat_s{i} rej 3 3 -norm=mul -32b -out={masters_path}/pp_flat_s{i}_stacked")
        else:
            self.siril.log(f"No Calibration (No Master Bias)", s.LogColor.GREEN)
            self.siril.cmd("stack", f"flat_s{i} rej 3 3 -norm=mul -32b -out={masters_path}/pp_flat_s{i}_stacked")  
        i += 1       
        self.siril.log("FINISHED CREATING MASTER FLATS.", s.LogColor.GREEN)

class RcPreprocessingInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle(f"{TITLE} - v{VERSION}")
        self.setStyleSheet(DARK_THEME_STYLESHEET)
        
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
        require_version = "1.4.2"
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
        title_label.setObjectName("titleLabel")
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
        bias_group = QGroupBox("Select Bias session files OR Bias Path OR Master Bias File")
        bias_layout = QVBoxLayout()
        bias_group.setLayout(bias_layout)
        
        # Bias session files
        self.bias_session_var = QCheckBox("Use bias session files (biases folder in each session)", self)
        self.bias_session_var.setChecked(False)
        
        bias_layout.addWidget(self.bias_session_var)
        
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
        dark_group = QGroupBox("Select Dark session files OR Dark Path OR Master Dark File")
        dark_layout = QVBoxLayout()
        dark_group.setLayout(dark_layout)
        
        # Dark session files
        self.dark_session_var = QCheckBox("Use dark session files (darks folder in each session)", self)
        self.dark_session_var.setChecked(False)
        
        dark_layout.addWidget(self.dark_session_var)
        
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

        # Flat group
        flat_group = QGroupBox("Flats")
        flat_layout = QVBoxLayout()
        flat_group.setLayout(flat_layout)

        self.no_flats_var = QCheckBox("No flats", self)
        self.no_flats_var.setChecked(False)

        flat_layout.addWidget(self.no_flats_var)

        container_child_1_layout.addWidget(flat_group)
        
        # 2 container_v
        #container_child_2_group = QGroupBox()
        container_child_2_layout = QVBoxLayout()
        #container_child_2_group.setLayout(container_child_2_layout)
        #container_layout.addWidget(container_child_2_group)
        container_layout.addLayout(container_child_2_layout)
        
        # Set bit dept
        bit_dept_group = QGroupBox("Choose bit dept preprocess mode")
        bit_dept_layout = QVBoxLayout()
        bit_dept_group.setLayout(bit_dept_layout)
        
        # Checkbox set bit dept
        self.bit_dept_16_var = QRadioButton("16 bit", self)
        self.bit_dept_32_var = QRadioButton("32 bit", self)
        self.bit_dept_32_var.setChecked(True)
        
        bit_dept_layout.addWidget(self.bit_dept_16_var)
        bit_dept_layout.addWidget(self.bit_dept_32_var)
        
        container_child_2_layout.addWidget(bit_dept_group)
        
        # Set drizzle
        drizzle_group = QGroupBox("Drizzle")
        drizzle_layout = QVBoxLayout()
        drizzle_group.setLayout(drizzle_layout)
        
        # Checkbox set drizzle
        self.drizzle_var = QCheckBox("Drizzle", self)
        self.drizzle_var.setChecked(False)
        
        drizzle_scale_label = QLabel("Scale")
        self.drizzle_scale_var = QComboBox()
        self.drizzle_scale_var.addItems(["1.0", "1.5","2.0", "2.5", "3.0"])
        
        drizzle_pixfrac_label = QLabel("Pixel fraction")
        self.drizzle_pixfrac_var = QComboBox()
        self.drizzle_pixfrac_var.addItems(["0.5", "0.55", "0.6", "0.65", "0.7", "0.75", "0.8", "0.85", "0.9", "0.95", "1.0"])
        
        drizzle_kernel_label = QLabel("Kernel")
        self.drizzle_kernel_var = QComboBox()
        self.drizzle_kernel_var.addItems(["square", "point", "turbo", "gaussian", "Lanczos2", "Lanczos3"])
        
        drizzle_layout.addWidget(self.drizzle_var)
        drizzle_layout.addWidget(drizzle_scale_label)
        drizzle_layout.addWidget(self.drizzle_scale_var)
        drizzle_layout.addWidget(drizzle_pixfrac_label)
        drizzle_layout.addWidget(self.drizzle_pixfrac_var)
        drizzle_layout.addWidget(drizzle_kernel_label)
        drizzle_layout.addWidget(self.drizzle_kernel_var)
        
        container_child_2_layout.addWidget(drizzle_group)
        
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
        submit_button.setObjectName("applyButton")
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
            "    ../object_folder/session_folder1/flats/ (optional with No Flats)\n"
            "                             /session_folder1/lights/\n"
            "                             /session_folder1/biases/ (optional)\n"
            "                             /session_folder1/darks/ (optional)\n"
            "                             /session_folder2/flats/ (optional with No Flats)\n"
            "                             /session_folder2/lights/\n"
            "                             /session_folder2/biases/ (optional)\n"
            "                             /session_folder2/darks/ (optional)\n\n"
            "2. Choose folder for processing.\n"
            "    The script creates here a /process, /masters\n"
            "    and /all_lights folder.\n"
            "    If more then 2000 lights on windows the script will\n"
            "    create batch folders of max 2000 files\n"
            "3. Choose in session biases folder or choose separately\n"
            "    a bias files folder or master bias file.\n"
            "    If blank preprocessing without master bias.\n"
            "4. Choose in session darks folder or choose seperately\n"
            "    a dark files folder or master dark file.\n"
            "    If blank preprocessing without master dark.\n"
            "5. Option for preprocessing without flats.\n"
            "6. Option for setting the images bitdept for preprocessing.\n"
            "    Master stack always saved in 32 bit.\n"
            "7. Option for drizzle.\n"
            "8. Options for cleaning up processing folders.\n"
            "9. Option for creating only a master bias file\n"
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
        bit_dept_32_var = self.bit_dept_32_var.isChecked()
        masters_path = Path(process_path_var).joinpath(masters_pattern)
        flats_path = Path(object_path_var).joinpath(flats_pattern)
        drizzle_var = self.drizzle_var.isChecked()
        drizzle_scale_var = self.drizzle_scale_var.currentText()
        drizzle_pixfrac_var = self.drizzle_pixfrac_var.currentText()
        drizzle_kernel_var = self.drizzle_kernel_var.currentText()
        print (drizzle_var)
        print (drizzle_scale_var)
        print (drizzle_pixfrac_var)
        print (drizzle_kernel_var)
        
    def run_apply(self):
        try:
            object_path_var = self.object_path_var.text().strip()
            process_path_var = self.process_path_var.text().strip()
            bias_session_var = self.bias_session_var.isChecked()
            bias_path_var = self.bias_path_var.text().strip()
            bias_file_var = self.bias_file_var.text().strip()
            dark_session_var = self.dark_session_var.isChecked()
            dark_path_var = self.dark_path_var.text().strip()
            dark_file_var = self.dark_file_var.text().strip()
            no_flats_var = self.no_flats_var.isChecked()
            process_cleanup_var = self.process_cleanup_var.isChecked()
            all_pp_lights_cleanup_var = self.all_pp_lights_cleanup_var.isChecked()
            create_bias_var = self.create_bias_var.isChecked()
            create_dark_var = self.create_dark_var.isChecked()
            bias_cleanup_var = self.bias_cleanup_var.isChecked()
            darks_cleanup_var = self.darks_cleanup_var.isChecked()
            flats_cleanup_var = self.flats_cleanup_var.isChecked()
            lights_cleanup_var = self.lights_cleanup_var.isChecked()
            bit_dept_32_var = self.bit_dept_32_var.isChecked()
            drizzle_var = self.drizzle_var.isChecked()
            drizzle_scale_var = self.drizzle_scale_var.currentText()
            drizzle_pixfrac_var = self.drizzle_pixfrac_var.currentText()
            drizzle_kernel_var = self.drizzle_kernel_var.currentText()

            if bit_dept_32_var == True:
                set_bit_dept = "set32bits"
            else:
                set_bit_dept = "set16bits"
                
            if drizzle_var == True:
                master_stack = "$OBJECT:%s$_$STACKCNT:%d$x$EXPTIME:%d$sec_G$GAIN:%d$_O$OFFSET:%d$_T$CCD-TEMP:%d$°C_$DATE-OBS:dm12$_drizzle"
            else:
                master_stack = "$OBJECT:%s$_$STACKCNT:%d$x$EXPTIME:%d$sec_G$GAIN:%d$_O$OFFSET:%d$_T$CCD-TEMP:%d$°C_$DATE-OBS:dm12$"
            
            # Check if paths are selected
            if create_bias_var == True or create_dark_var == True:
                warning_messages = []
                if process_path_var in (None, "") or not Path(process_path_var).is_dir():
                    warning_messages.append("Select a valid process folder.")
                if create_bias_var == True:
                    if bias_path_var in (None, "") or not Path(bias_path_var).is_dir():
                        warning_messages.append("Select a valid bias folder.")
                    elif not folder_has_files(Path(bias_path_var)):
                        warning_messages.append(f"Bias folder is empty: {bias_path_var}")
                if create_dark_var == True:
                    if dark_path_var in (None, "") or not Path(dark_path_var).is_dir():
                        warning_messages.append("Select a valid dark folder.")
                    elif not folder_has_files(Path(dark_path_var)):
                        warning_messages.append(f"Dark folder is empty: {dark_path_var}")

                if warning_messages:
                    for warning_message in warning_messages:
                        self.siril.log(warning_message, s.LogColor.SALMON)
                    QMessageBox.warning(
                        self,
                        "Check Selections",
                        "Please correct:\n- " + "\n- ".join(warning_messages),
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
                        
            else:
                warning_messages = []

                if object_path_var in (None, "") or not Path(object_path_var).is_dir():
                    warning_messages.append("Select a valid object folder.")
                if process_path_var in (None, "") or not Path(process_path_var).is_dir():
                    warning_messages.append("Select a valid process folder.")

                bias_selections = [bias_session_var, bias_path_var != "", bias_file_var != ""]
                if sum(1 for selected in bias_selections if selected) > 1:
                    warning_messages.append("Select session bias files, bias folder, master bias file or none.")
                if bias_path_var != "" and not Path(bias_path_var).is_dir():
                    warning_messages.append(f"Select a valid bias folder: {bias_path_var}")
                if bias_file_var != "" and not Path(bias_file_var).is_file():
                    warning_messages.append(f"Select a valid master bias file: {bias_file_var}")

                dark_selections = [dark_session_var, dark_path_var != "", dark_file_var != ""]
                if sum(1 for selected in dark_selections if selected) > 1:
                    warning_messages.append("Select session dark files, dark folder, master dark file or none.")
                if dark_path_var != "" and not Path(dark_path_var).is_dir():
                    warning_messages.append(f"Select a valid dark folder: {dark_path_var}")
                if dark_file_var != "" and not Path(dark_file_var).is_file():
                    warning_messages.append(f"Select a valid master dark file: {dark_file_var}")

                if not warning_messages:
                    warning_messages.extend(
                        validate_session_frame_folders(
                            object_path_var,
                            no_flats_var,
                            bias_session_var,
                            dark_session_var
                        )
                    )

                if warning_messages:
                    for warning_message in warning_messages:
                        self.siril.log(warning_message, s.LogColor.SALMON)
                    QMessageBox.warning(
                        self,
                        "Check Selections",
                        "Please correct:\n- " + "\n- ".join(warning_messages),
                    )
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
                    if bias_session_var == True:
                        bias_master = create_session_master_bias(self, object_path_var, process_temp_path, masters_path)
                    elif Path(bias_file_var).is_file():
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

                    if dark_session_var == True:
                        dark_master = create_session_master_dark(self, object_path_var, process_temp_path, masters_path)
                    elif Path(dark_file_var).is_file():
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
                    if no_flats_var == True:
                        self.siril.log("No Master Flat.", s.LogColor.SALMON)
                    else:
                        create_master_flat(self, object_path_var, process_temp_path, bias_master, masters_path)

                        if flats_cleanup_var == True:
                            for path in Path(process_temp_path).rglob(flats_cleanup_pattern):
                                Path(path).unlink()
                            
                    # Preprocessing light frames                        
                    if drizzle_var == True:
                        debayer = ""
                    else:
                        debayer = "-debayer"
                        
                    object_array = get_session_paths(object_path_var)
                    i = 1
                    for object in object_array:        
                        session_bias_master = bias_master[i - 1] if isinstance(bias_master, list) else bias_master
                        session_dark_master = dark_master[i - 1] if isinstance(dark_master, list) else dark_master
                        
                        flat_calibration = "" if no_flats_var == True else f"-flat={masters_path}/pp_flat_s{i}_stacked -equalize_cfa"

                        if session_bias_master == "" and session_dark_master == "":
                            if no_flats_var == True:
                                self.siril.log(f"Calibrate session {i} without master calibration frames", s.LogColor.GREEN)
                            else:
                                self.siril.log(f"Calibrate session {i} with: Only Master Flat", s.LogColor.GREEN)
                            lights_calibration = ""
                        elif session_bias_master != "" and session_dark_master == "":
                            if no_flats_var == True:
                                self.siril.log(f"Calibrate session {i} with: Master Bias", s.LogColor.GREEN)
                            else:
                                self.siril.log(f"Calibrate session {i} with: Master Bias and Master Flat", s.LogColor.GREEN)
                            lights_calibration = f"-bias={session_bias_master}"
                        else:
                            if no_flats_var == True:
                                self.siril.log(f"Calibrate session {i} with: Master Dark", s.LogColor.GREEN)
                            else:
                                self.siril.log(f"Calibrate session {i} with: Master Dark and Master Flat", s.LogColor.GREEN)
                            lights_calibration = f"-dark={session_dark_master}"
                        
                        self.siril.cmd("cd", f"{object.joinpath(lights_pattern)}")
                        self.siril.cmd("convert", f"light_s{i} -out={process_temp_path}")
                        self.siril.cmd("cd", f"{process_temp_path}")
                        self.siril.cmd("calibrate", f"light_s{i} {lights_calibration} {flat_calibration} -cfa {debayer}")
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
                        
                        self.siril.cmd("cd", f"{all_pp_lights_temp_path}")
                        self.siril.cmd("convert", f"all_light -out={process_temp_path}")
                        self.siril.cmd("cd", f"{process_temp_path}")
                        self.siril.cmd("register", "all_light")
                        if drizzle_var == True:
                            self.siril.cmd("seqapplyreg", f"all_light -drizzle -scale={drizzle_scale_var} -pixfrac={drizzle_pixfrac_var} -kernel={drizzle_kernel_var}")    
                        self.siril.cmd("stack", f"r_all_light rej 3 3 -norm=addscale -output_norm -rgb_equal -32b -out={masters_path}/{master_stack}")
                        
                        self.siril.cmd("cd", f"{masters_path}")
                        
                        self.siril.log("FINISHED OSC PREPROCESSING.", s.LogColor.GREEN)
                        
                        self.siril.cmd("set32bits")
                    else:
                        # Create batch folders
                        batch_temp_path.mkdir(exist_ok=True)
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
                            self.siril.cmd("convert", f"all_light_{i} -out={process_temp_path}")
                            self.siril.cmd("cd", process_temp_path)
                            self.siril.cmd("register", f"all_light_{i}")
                            if drizzle_var == True:
                                self.siril.cmd("seqapplyreg", f"all_light_{i} -drizzle -scale={drizzle_scale_var} -pixfrac={drizzle_pixfrac_var} -kernel={drizzle_kernel_var}")    
                            self.siril.cmd("stack", f"r_all_light_{i} rej 3 3 -norm=addscale -output_norm -rgb_equal -32b -out={batch_temp_path}/batch_light_all_{i}")
                            i += 1
                            
                        self.siril.cmd("cd", batch_temp_path)
                        self.siril.cmd("convert", f"batch_all_light -out={process_temp_path}")
                        self.siril.cmd("cd", process_temp_path)
                        #self.siril.cmd("register", f"batch_all_light")
                        self.siril.cmd("seqplatesolve", f"batch_all_light")
                        self.siril.cmd("seqapplyreg", f"batch_all_light")
                        self.siril.cmd("stack", f"r_batch_all_light rej 3 3 -norm=addscale -output_norm -rgb_equal -32b -out={masters_path}/{master_stack}")
                        
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




