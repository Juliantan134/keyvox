import sys
import os
from file_protector import encrypt_file

def main():
    """
    This script encrypts a target file and creates a .bat launcher 
    to open it through the KeyVox authenticator app.
    """
    # 1. Check if a file path was provided as an argument.
    if len(sys.argv) < 2:
        print("Usage: python lock_file.py \"<path_to_your_file>\"")
        print("Tip: You can also drag and drop a file onto this script.")
        return

    target_file = sys.argv[1]
    
    # 2. Verify the file actually exists.
    if not os.path.exists(target_file):
        print(f"Error: File not found at '{target_file}'")
        return

    # 3. Encrypt the file using the function from our protector module.
    #    This will create 'yourfile.ext.locked' and delete the original.
    print(f"Locking '{os.path.basename(target_file)}'...")
    locked_file_path = encrypt_file(target_file)
    
    # 4. Define the paths needed to create the launcher.
    #    CHANGE 'app.py' TO 'run_authenticator.py'
    launcher_py_path = os.path.abspath("run_authenticator.py") 
    python_exe_path = sys.executable
    
    # 5. Create the name and path for the new launcher file.
    #    For "MyReport.docx", this will create "Unlock MyReport.bat".
    launcher_name = "Unlock " + os.path.splitext(os.path.basename(target_file))[0]
    launcher_path = os.path.join(os.path.dirname(locked_file_path), f"{launcher_name}.bat")
    
     # 6. Build the command that the .bat file will execute.
    #    It now runs: python.exe run_authenticator.py "path\to\locked\file"
    batch_command = f'@echo off\n"{python_exe_path}" "{launcher_py_path}" "{locked_file_path}"' 
    
    # 7. Write the command to the .bat file.
    with open(launcher_path, "w") as launcher_file:
        launcher_file.write(batch_command)
        
    print("-" * 30)
    print("✅ Success! Your file has been secured.")
    print(f"A new launcher has been created:\n  -> {launcher_path}")
    print("\nUse this launcher to unlock your file with your Pico and voice.")

if __name__ == "__main__":
    main()





