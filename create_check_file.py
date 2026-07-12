import subprocess

command = "echo 'Validated API' > check.txt"

try:
    subprocess.run(command, shell=True, check=True)  # nosec
    print("File 'check.txt' created successfully with content 'Validated API'.")
except subprocess.CalledProcessError as e:
    print(f"Error creating file: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
