import subprocess
import sys
import os
import shutil
import urllib.request
import zipfile
import platform

def install_python_packages():
    # Define the required Python packages
    python_packages = [
        "certipy-ad",
        "impacket"
    ]

    # Install Python packages using pip
    for package in python_packages:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def check_script_installed(script_name):
    """Check if a script is installed in the impacket examples folder."""
    try:
        impacket_path = os.path.join(os.path.dirname(sys.executable), 'lib', 'python' + sys.version[:3], 'site-packages', 'impacket', 'examples', script_name)
        if os.path.exists(impacket_path):
            return True
        return False
    except (FileNotFoundError, PermissionError):
        return False

def download_file(url, save_path):
    urllib.request.urlretrieve(url, save_path)

def download_and_extract(url, extract_to='.'):
    file_name = url.split('/')[-1]
    urllib.request.urlretrieve(url, file_name)
    if file_name.endswith('.zip'):
        with zipfile.ZipFile(file_name, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        os.remove(file_name)

def clone_repository(repo_url, clone_to):
    if os.path.exists(clone_to):
        print(f"Directory {clone_to} already exists. Cleaning up the directory.")
        subprocess.check_call(['rm', '-rf', clone_to])
    subprocess.check_call(['git', 'clone', repo_url, clone_to])

def install_netexec():
    try:
        if platform.system() == 'Windows':
            print("NetExec installation script currently does not support Windows.")
            sys.exit(1)
        subprocess.check_call(["sudo", "apt", "install", "-y", "pipx", "git"])
        subprocess.check_call(["pipx", "ensurepath"])
        subprocess.check_call(["pipx", "install", "git+https://github.com/Pennyw0rth/NetExec"])

        # Ensure PATH is updated
        ensure_path_command = subprocess.check_output(["pipx", "ensurepath"]).decode()
        if 'needs to be added to' in ensure_path_command:
            print("Adding pipx bin to PATH")
            shell_config_file = os.path.expanduser("~/.bashrc")
            with open(shell_config_file, "a") as file:
                file.write('\n# Add pipx bin to PATH\n')
                file.write('export PATH="$HOME/.local/bin:$PATH"\n')
            subprocess.run(["source", shell_config_file], shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to install NetExec: {e}")
        sys.exit(1)

def install_non_python_dependencies():
    tools = {
        "certipy": "https://github.com/ly4k/Certipy/archive/refs/heads/master.zip",
        "petitpotam": "https://github.com/topotam/PetitPotam.git",
    }

    home_dir = os.path.expanduser("~")
    
    for tool, url in tools.items():
        if tool == "petitpotam":
            # Always clone petitpotam since we can't check if it is installed by default
            print(f"Downloading and installing {tool}...")
            clone_repository(url, os.path.join(home_dir, 'PetitPotam'))
        else:
            if not check_script_installed(f"{tool}.py"):
                print(f"{tool}.py not found. Downloading and installing...")
                download_and_extract(url, home_dir)

    if not check_script_installed("netexec.py"):
        print("NetExec not found. Installing via pipx...")
        install_netexec()

    # Download scanner.py for checking machine account quota
    scanner_url = "https://raw.githubusercontent.com/Ridter/noPac/main/scanner.py"
    scanner_path = os.path.join(home_dir, "scanner.py")
    if not os.path.exists(scanner_path):
        print("Downloading scanner.py...")
        download_file(scanner_url, scanner_path)

def verify_installation():
    # Check if scanner.py is installed
    home_dir = os.path.expanduser("~")
    scanner_path = os.path.join(home_dir, "scanner.py")
    if not os.path.exists(scanner_path):
        print(f"Error: scanner.py is not installed. Please ensure it is installed and accessible in the PATH.")
        return False

    print("All required tools are installed.")
    return True

if __name__ == "__main__":
    install_python_packages()
    install_non_python_dependencies()

    if verify_installation():
        print("All dependencies are installed and verified.")
    else:
        print("Some dependencies are missing. Please install them and try again.")
