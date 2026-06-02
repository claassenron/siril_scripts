OSC PREPROCESSING SCRIPT FOR SIRIL 1.4.2

<img width="1107" height="935" alt="Schermafbeelding 2026-06-02 140018" src="https://github.com/user-attachments/assets/538df6a1-1e1f-4568-83d2-3871b0d7cde7" />

THIS SCRIPT DOES NOT MOVE OR MAKES CHANGES TO ANY OF THE SOURCE FILES

MULTI SESSION PREPROCESSING IS POSSIBLE.

1. Choose Object folder.
    Folder structure:

   ../object_folder/session_folder1/flats/

   ............................./session_folder1/lights/
   
   ............................./session_folder2/flats/
   
   ............................./session_folder2/lights/

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

3. Choose bias files folder or master bias file.
If blank, preprocessing without master bias.

4. Choose dark files folder or master dark file.
If blank, preprocessing without master dark.

5. Option for setting the images bit dept for preprocessing.
Master stack always saved in 32 bit.

6. Option for drizzle

7. Options for cleaning up processing folders.

8. Option for creating only a master bias file and/or master dark file.
