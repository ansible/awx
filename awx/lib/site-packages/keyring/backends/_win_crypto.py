
from ctypes import Structure, POINTER, c_void_p, cast, create_string_buffer, \
    c_char_p, byref, memmove
from ctypes import windll, WinDLL, WINFUNCTYPE
try:
    from ctypes import wintypes
except ValueError:
    # see http://bugs.python.org/issue16396
    raise ImportError("wintypes")

from keyring.util.escape import u

# Crypto API ctypes bindings

class DATA_BLOB(Structure):
    _fields_ = [('cbData', wintypes.DWORD),
                ('pbData', POINTER(wintypes.BYTE))]


class CRYPTPROTECT_PROMPTSTRUCT(Structure):
    _fields_ = [('cbSize', wintypes.DWORD),
                ('dwPromptFlags', wintypes.DWORD),
                ('hwndApp', wintypes.HWND),
                ('szPrompt', POINTER(wintypes.WCHAR))]

# Flags for CRYPTPROTECT_PROMPTSTRUCT

CRYPTPROTECT_PROMPT_ON_UNPROTECT = 1
CRYPTPROTECT_PROMPT_ON_PROTECT = 2

# Flags for CryptProtectData/CryptUnprotectData

CRYPTPROTECT_UI_FORBIDDEN = 0x01
CRYPTPROTECT_LOCAL_MACHINE = 0x04
CRYPTPROTECT_CRED_SYNC = 0x08
CRYPTPROTECT_AUDIT = 0x10
CRYPTPROTECT_NO_RECOVERY = 0x20
CRYPTPROTECT_VERIFY_PROTECTION = 0x40
CRYPTPROTECT_CRED_REGENERATE = 0x80

# Crypto API Functions

_dll = WinDLL('CRYPT32.DLL')

CryptProtectData = WINFUNCTYPE(wintypes.BOOL,
                               POINTER(DATA_BLOB),
                               POINTER(wintypes.WCHAR),
                               POINTER(DATA_BLOB),
                               c_void_p,
                               POINTER(CRYPTPROTECT_PROMPTSTRUCT),
                               wintypes.DWORD,
                               POINTER(DATA_BLOB))(('CryptProtectData', _dll))

CryptUnprotectData = WINFUNCTYPE(wintypes.BOOL,
                                 POINTER(DATA_BLOB),
                                 POINTER(wintypes.WCHAR),
                                 POINTER(DATA_BLOB),
                                 c_void_p,
                                 POINTER(CRYPTPROTECT_PROMPTSTRUCT),
                                 wintypes.DWORD, POINTER(DATA_BLOB))(
                                         ('CryptUnprotectData', _dll))

# Functions


def encrypt(data, non_interactive=0):
    blobin = DATA_BLOB(cbData=len(data),
                       pbData=cast(c_char_p(data),
                                   POINTER(wintypes.BYTE)))
    blobout = DATA_BLOB()

    if not CryptProtectData(byref(blobin),
                            u('python-keyring-lib.win32crypto'),
                            None, None, None,
                            CRYPTPROTECT_UI_FORBIDDEN,
                            byref(blobout)):
        raise OSError("Can't encrypt")

    encrypted = create_string_buffer(blobout.cbData)
    memmove(encrypted, blobout.pbData, blobout.cbData)
    windll.kernel32.LocalFree(blobout.pbData)
    return encrypted.raw


def decrypt(encrypted, non_interactive=0):
    blobin = DATA_BLOB(cbData=len(encrypted),
                       pbData=cast(c_char_p(encrypted),
                                   POINTER(wintypes.BYTE)))
    blobout = DATA_BLOB()

    if not CryptUnprotectData(byref(blobin),
                              u('python-keyring-lib.win32crypto'),
                              None, None, None,
                              CRYPTPROTECT_UI_FORBIDDEN,
                              byref(blobout)):
        raise OSError("Can't decrypt")

    data = create_string_buffer(blobout.cbData)
    memmove(data, blobout.pbData, blobout.cbData)
    windll.kernel32.LocalFree(blobout.pbData)
    return data.raw
