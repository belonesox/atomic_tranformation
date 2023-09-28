"""Main module."""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  Collection of all auxiliary utilities.
"""
import sys
import os
import time
import datetime
import pytz
import re
import shutil
import errno
import stat
import subprocess
import pickle
import glob
import trans
import inspect
import threading
#import threading

IS_WINDOWS = (os.name == 'nt')

def file_is_ok(filepath):
    """
      Simple checks a file ``filepath`` exists and has nonzero size.
    """
    return os.path.exists(filepath) and os.stat(filepath).st_size>0

def need_update(target, source, update_time = None):
    """
     Simple refresh condition for target file
    """
    if not os.path.exists(source):
        return False
    source_time = os.stat(source).st_mtime
    if update_time:
        source_time = max(update_time, source_time)
    res = not file_is_ok(target) or     os.stat(target).st_mtime < source_time
    if res:
        pass
    return res

def hash4string(astr, salt=None):
    '''
    Sha1 hash for string, simple call.
    '''
    ustr = astr.encode('utf-8')
    import hashlib
    m = hashlib.sha1()   # Perfectionist can use sha224.
    m.update(ustr)
    return m.hexdigest()[:16]


def short_uniq_filename(source):
    '''
        Made short uniq filename, need for filesystems with Max Path, and for utilities (like ffmpeg)
        working reliable only with ASCII filenames
    '''
    ufilename = source
    dirname, nameext = os.path.split(ufilename)
    sshortname = '-'.join([trans.trans(nameext[:8]), 
                           hash4string(nameext), 
                           trans.trans(nameext[-4:])])
    return os.path.join(dirname, sshortname) 

def short_uniq_filename_ext(source):
    '''
        Made short uniq filename, need for filesystems with Max Path, and for utilities (like ffmpeg)
        working reliable only with ASCII filenames
    '''
    ufilename = source
    dirname, nameext = os.path.split(ufilename)
    sshortname = '-'.join([trans.trans(nameext[:4]), 
                           hash4string(nameext), 
                           trans.trans(nameext[-64:])])
    return os.path.join(dirname, sshortname) 
    

def transaction(target, source, action, options=None,  update_time = None, locktarget = True):
    """
      Simple and lazy transactional refresh mechanism.
      If source refreshed:
        target = action(source)
    """
    if not need_update(target, source, update_time):
        return

    directory, nameext = os.path.split(target)
    sshortname = short_uniq_filename(nameext)
    shortname = short_uniq_filename_ext(nameext)
    if len(nameext)<len(shortname):
        shortname = nameext    
    lock_dir  = os.path.join(directory, "~~" + sshortname + '.!')
    lock_file = os.path.join(lock_dir, 'lock')
    tmp  = os.path.join(lock_dir, "~~" + shortname)
    createdir(directory)

    lock_file = os.path.join(lock_dir, 'lock')
    if os.path.exists(lock_dir):
        try:
            removedirorfile(lock_dir)
        except Exception:
            raise Exception('Target "' + target +'" locked.')
    

    createdir(lock_dir)
#    print "Thread ",  threading.current_thread(), " lock ", lock_file
    lock_handle = open(lock_file, 'w')
    hidefile(lock_dir)

    res_act = False
    if len(inspect.signature(action).parameters) == 3:
        res_act = action(tmp, source, options)
    else:    
        res_act = action(tmp, source)
    if res_act and file_is_ok(tmp):
        if os.path.exists(target):
            bak = os.path.join(directory, "~~bak--" + nameext)
            if os.path.exists(bak):
                os.unlink(bak)
            os.rename(target, bak)
            hidefile(bak)
        shutil.move(tmp, target)

    lock_handle.close()
#    print "Thread ",  threading.current_thread(), " unlock ", lock_file
    removedirorfile(lock_dir)


def do_in_dir(dir_, action):
    '''
    Go to some directory and perform some function thread safe
    '''
    try:
        chdir_lock = threading.Lock()
        with chdir_lock:
            curdir = os.getcwd()
            os.chdir(dir_)
            res = action()
            os.chdir(curdir)
            return res
    except Exception as ex_:
        print("Troubles with action in dir", dir_)
        raise ex_



def createdir(dirpath):
    """
     Create directory with parent directories.
    """
    if not os.path.exists(dirpath):
        #print "Try to create ", dirpath
        try:
            os.mkdir(dirpath)
        except OSError:
            (path, dir_) = os.path.split(dirpath)
            if dir_ != "":
                createdir(path)
                os.mkdir(dirpath)


def handle_remove_readonly(func, path, exc):
    """
    To kill read-only files.
    """
    excvalue = exc[1]
    if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
        func(path)
    else:
        raise

def removedirorfile(p, olderthan=None):
    """
      Try to silently remove file or recursively remove directory,
      ignoring errors and warnings.
    """
    def _onerror(func, path, exc_info):
        """
        Make readonly files writeable and try to resume deletion.
        """
        # print "error on path", path
        # print exc_info
        # time.sleep(2000)
        if not os.access(path, os.W_OK):
            # Is the error an access error ?
            os.chmod(path, stat.S_IWUSR)
            func(path)
        else:
            raise exc_info

    if type(p) == type([]):
        for pp in p:
            removedirorfile(pp)
    else:
        if not os.path.exists(p):
            return
        if os.path.isdir(p):
            # scmd = "handle " + os.path.abspath(p)
            # os.system(scmd)
            shutil.rmtree(p, ignore_errors=False, onerror=_onerror)
            # for try_ in xrange(1):
            #     try:
            #         shutil.rmtree(p, ignore_errors=False, onerror=_onerror)
            #         break
            #     except:
            #         time.sleep(2)
            #         pass
        else:
            needremove = True
            if olderthan:
                dt  = os.stat(p).st_ctime
                needremove = dt < olderthan
            if needremove:
                os.unlink(p)

def compare_by_creation_time(file1, file2):
    """
      compare two files by creation time.
      if creation time equals, comparing modification time.
    """
    if not os.path.exists(file1) or not os.path.exists(file2):
        return 0
    res = int((os.stat(file1).st_ctime - os.stat(file2).st_ctime) * 1000)
    if not res:
        res = int((os.stat(file1).st_mtime - os.stat(file2).st_mtime) * 1000)
    return res


def search_file(thefilename, search_path):
    """
    Find file in given path. Comparing case unsensitive.
    """
    for root, _dirnames, filenames in os.walk(search_path):
        if thefilename.lower() in [f.lower() for f in filenames + _dirnames]:
            return os.path.join(search_path, root, thefilename)
    return None


def hidefile(filepath):
    '''
    Hide file, now work only for Windows
    '''
    if IS_WINDOWS:
        try:
            import win32con, win32api
            win32api.SetFileAttributes(filepath, win32con.FILE_ATTRIBUTE_HIDDEN)
        except:
            pass

def unhidefile(filepath):
    '''
    Unhide file, now work only for Windows
    '''
    if IS_WINDOWS:
        try:
            import win32con, win32api
            win32api.SetFileAttributes(filepath, win32con.FILE_ATTRIBUTE_NORMAL)
        except:
            pass


