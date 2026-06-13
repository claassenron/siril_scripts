OSC PREPROCESSING SCRIPT FOR SIRIL 1.4.2

<img width="1102" height="1073" alt="Schermafbeelding 2026-06-13 151507" src="https://github.com/user-attachments/assets/0c72cd14-aece-44cc-a3f2-04602f5a13fa" />

THIS SCRIPT DOES NOT MOVE OR MAKES CHANGES TO ANY OF THE SOURCE FILES

MULTI SESSION PREPROCESSING IS POSSIBLE.

1. Choose Object folder.
    Folder structure:

   ../object_folder/session_folder1/flats/ (optional with No Flats)
   ............................./session_folder1/lights/

   ............................./session_folder1/biases/ (optional)

   ............................./session_folder1/darks/ (optional)
   
   ............................./session_folder2/flats/ (optional with No Flats)
   
   ............................./session_folder2/lights/

   ............................./session_folder2/biases/ (optional)

   ............................./session_folder2/darks/ (optional)

    Folder structure example:

    ../NGC7380/2025-08-08/flats/

    ..........|............./.........|........../lights/

    ..........|............./2025-08-10/flats/

    ..........|............./.........|........../lights/

    ..........|............./2025-08-12/flats/

    ..........|............./.........|........./lights/

2. Choose folder for processing.
The script creates here a /process, /masters and /all_lights folder.
If more then 2000 lights on Windows OS the script will create batch folders of max 2000 files.

3. Choose in session biases folder or choose separately a bias files folder or master bias file.
If blank, preprocessing without master bias.

4. Choose in session darks folder or choose seperately a dark files folder or master dark file.
If blank, preprocessing without master dark.

5. Option for preprocessing without flats.

6. Option for setting the images bit dept for preprocessing.
Master stack always saved in 32 bit.

7. Option for drizzle

8. Options for cleaning up processing folders.

9. Option for creating only a master bias file and/or master dark file.
