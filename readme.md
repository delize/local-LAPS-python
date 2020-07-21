# Note: Deprecated
As of macOS 10.13/14, this tool no longer works due to SIP protection on the location of the file that this was editing. This is merely a proof of concept now. If you are deploying devices older than 10.13, this tool will still work, however I would highly recommend upgrading your deployment solution.

# Local Admin Password Solution - MAC (MacLAPS)
When deploying laptops having a repeatable, manageable, scriptable solution to generate and list passwords for devices. This specific LAPS deals with Macs but the code can be modified or altered to check for a specific operating system and generate passwords that way.

## Problem
Every device has the same administrator password. This isn't secure, scalable, or helpful.

## What does this fix?
If we need to give out the admin password for any reason, this allows us to do so, and generate a new password for replacement of the admin user per device.
# Usage
## For deployments
The current way we are doing this for deployment is through the following:
1. Create a virtual env
2. Install pip modules into venv
3. Place files into venv
4. Package venv
5. Place on deployment server

## For generating passwords
Currently you will need to modify your file to properly generate a password without removing the directory that the salt is placed in (which if done appropriately, should be the same folder your python script is).

**Requirements**
- Have a brew-compatible/installed python

**Known compatible pip modules**
- pyobjc 4.1
- biplist 1.0.3
- passlib  1.7.1

**Directions**

1. Git clone this repository.
2. Run `pip install -r requirements.txt`
3. Use your favorite text editor and change the following lines (for now):
 - Line 83 - modify `/tmp/password_gen_secrets/salt.file` to the path of your salt file location
 - Line 88 - modify `default=True` to `default=False`
 - Line 101 - modify `default=False` to `default=True`

 This will allow you to generate passwords for one time use on a new line in the console.

4. Run the following command: `python lapsmac.py -sn SERIALNUMBERHERE`
5. Type or give out administrator password for use

