# MAQ-Attaq
A python script to automate an Active Directory attack path levearging MAQ, Web Enrollment and RBCD. FOR EDUCATIONAL PURPOSES ONLY.

# TLDR
This approach is intended for scenarios where a domain admin session is identified on a server or domain-joined computer. By leveraging a misconfigured Machine Account Quota (MAQ), you can create a machine account. Then, utilizing an insecure Active Directory Certificate Services (ADCS) server vulnerable to ESC8, you can obtain the NTLM hash of the target server or computer's machine account. With this NTLM hash, you can leverage Resource-Based Constrained Delegation (RBCD) to modify the msDS-AllowedToActOnBehalfOfOtherIdentity attribute, allowing the machine account you created to impersonate any user, preferably a domain admin, against the target machine account. This enables you to perform privileged actions such as dumping SAM or LSA Secrets.

# Setup

  1. Clone the repository
  ```
  git clone https://github.com/SnoopJesus420/MAQ-Attaq
  ```

  2. cd into directory
  ```
  cd MAQ-Attaq
  ```
  3. Setup a python virtual environment
  ```
  python3 -m venv venv && source venv/bin/activate
  ```
  4. Execute the setup script
  ```
  python3 depends.py
  ```

# Execution
```
python3 maq-attaq.py
```

# Resources
https://www.thehacker.recipes/ad/movement/domain-settings/machineaccountquota <br>
https://book.hacktricks.xyz/windows-hardening/active-directory-methodology/resource-based-constrained-delegation <br>
https://ppn.snovvcrash.rocks/pentest/infrastructure/ad/ad-cs-abuse/esc8

