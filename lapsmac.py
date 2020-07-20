#!/usr/bin/env python

import sys
import hashlib, biplist, argparse, os.path, objc, shutil
from passlib.hash import pbkdf2_sha512
from passlib.utils.binary import ab64_decode
from biplist import *
from Foundation import NSBundle
from Foundation import NSPropertyListSerialization
from Foundation import NSPropertyListXMLFormat_v1_0
from Foundation import NSPropertyListBinaryFormat_v1_0

sys.path.append('/tmp/password_gen')
'''
plist utility functions - Taken from Greg Neagle
https://github.com/gregneagle/pycreateuserpkg/blob/master/locallibs/plistutils.py
'''


class FoundationPlistException(Exception):
    """Basic exception for plist errors"""
    pass


def write_plist(dataObject, pathname=None, plist_format=None):
    '''
    Write 'rootObject' as a plist to pathname or return as a string.
    '''
    if plist_format == 'binary':
        plist_format = NSPropertyListBinaryFormat_v1_0
    else:
        plist_format = NSPropertyListXMLFormat_v1_0

    plistData, error = (
        NSPropertyListSerialization.
        dataFromPropertyList_format_errorDescription_(
            dataObject, plist_format, None))
    if plistData is None:
        if error:
            error = error.encode('ascii', 'ignore')
        else:
            error = "Unknown error"
        raise FoundationPlistException(error)
    if pathname:
        if plistData.writeToFile_atomically_(pathname, True):
            return
        else:
            raise FoundationPlistException(
                "Failed to write plist data to %s" % filepath)
    else:
        return plistData


def get_mac_serial_number():
    '''
    Returns the serial number of this Mac.
    Stolen from someone on Github - didn't write it down
    https://github.com/chilcote/unearth/blob/cefea89db6e2ca45b73a731672174c66fedd6aa1/artifacts/serial_number.py
    '''
    IOKit_bundle = NSBundle.bundleWithIdentifier_("com.apple.framework.IOKit")

    functions = [
        ("IOServiceGetMatchingService", b"II@"),
        ("IOServiceMatching", b"@*"),
        ("IORegistryEntryCreateCFProperty", b"@I@@I")
    ]
    objc.loadBundleFunctions(IOKit_bundle, globals(), functions)

    kIOMasterPortDefault = 0
    kIOPlatformSerialNumberKey = 'IOPlatformSerialNumber'
    kCFAllocatorDefault = None

    platformExpert = IOServiceGetMatchingService(kIOMasterPortDefault,
                                                 IOServiceMatching("IOPlatformExpertDevice"))
    serial = IORegistryEntryCreateCFProperty(platformExpert,
                                             kIOPlatformSerialNumberKey,
                                             kCFAllocatorDefault, 0)
    return serial


def parse_args():
    parser = argparse.ArgumentParser(description="Process user input for serial number, salt file, actual salt, nonce")
    # The default is intended to be used with DeployStudio
    parser.add_argument('-f', '--salt_file', type=str,
                        default='/Users/adoering/Documents/Github/LAPSmac/salt.mac',
                        help='Path to the file containing the salt')
    parser.add_argument('-sn', '--serial_number', type=str,
                        default="{}".format(get_mac_serial_number()),
                        help='mac serial number')
    parser.add_argument('-p', '--plist', type=bool, default=False,
                        help='Automatically generate the plist')
    parser.add_argument('-pf', '--plist_file', type=str,
                        default='/var/db/dslocal/nodes/Default/users/administrator.plist',
                        help='User plist path. Defaults to the administrator user.')
    parser.add_argument('-n', '--nonce', type=str, default="1",
                        help='Different nonces generate completely different results')
    parser.add_argument('-c', '--checksum-size', type=int, default=128,
                        help='pbkdf2_sha512 checksum size. Defaults to 128.')
    parser.add_argument('-r', '--rounds', type=int, default=200000,
                        help='pbkdf2_sha512 encrypt rounds. Defaults to 200000.')
    parser.add_argument('-ss', '--salt_size', type=int, default=32,
                        help='pbkdf2_sha512 encrypt salt_size. Defaults to 32.')
    parser.add_argument('-sp', '--show_password', type=bool, default=True,
                        help='Show the generated password. Defaults to False')

    args = parser.parse_args()
    return (args.salt_file, args.serial_number, args.nonce, args.plist,
            args.plist_file, args.checksum_size, args.rounds, args.salt_size, args.show_password)


def gen_password(serial_number, salt, nonce, length=32):
    return hashlib.sha512(serial_number + salt + nonce).hexdigest()[:length]


if __name__ == '__main__':
    (salt_file, serial_number, nonce, plist, plist_file,
     checksum_size, rounds, salt_size, show_password) = parse_args()

    if not os.path.isfile(salt_file):
        print "Error: {} does not exist!".format(salt_file)
        sys.exit(1)

    with open(salt_file, 'r') as f:
        salt = f.read().strip('\n')

    password = gen_password(serial_number, salt, nonce)
    if show_password:
        print password

    if plist:
        # Remove the salt folder and it's contents
        shutil.rmtree(os.path.dirname(salt_file))
        # Show password during automation run - only useful for debugging
        pbkdf2_sha512.checksum_size = checksum_size
        hash = pbkdf2_sha512.encrypt(password, rounds=rounds, salt_size=salt_size)
        shadow_hash_data = {'SALTED-SHA512-PBKDF2': {'entropy': buffer(Data(ab64_decode(hash.split('$')[4]))),
                                                   'salt': buffer(Data(ab64_decode(hash.split('$')[3]))),
                                                   'iterations': int(hash.split('$')[2])}}
        shadow_hash_data_binary = write_plist(shadow_hash_data, plist_format='binary')
        user_plist = biplist.readPlist(plist_file)
        try:
            user_plist['ShadowHashData'][0] = shadow_hash_data_binary
        except KeyError, error:
            print error
            sys.exit(1)
        write_plist(user_plist, pathname=plist_file, plist_format='binary')
    else:
        sys.exit(0)
