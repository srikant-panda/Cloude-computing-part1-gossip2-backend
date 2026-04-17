# #!/usr/bin/env python

# #**********************
# #*
# #* Progam Name: MP1. Membership Protocol.
# #*
# #* Current file: submit.py
# #* About this file: Submission python script.
# #* 
# #***********************

# # Originally designed for Python 2.
# # Updated 20191024 with Python2/3 compatibility hacks, further diagnostics
# # Updates by University of Illinois CS Instructional Design staff

# import hashlib
# import random
# import email
# import email.message
# import email.encoders
# # import StringIO # unused
# import sys
# import subprocess
# import json
# import os
# import os.path

# print('\nPLEASE NOTE: To work on this assignment, we assume you already know how to')
# print('program in C++, you have a working Bash shell environment set up (such as')
# print('Linux, or Windows 10 with WSL installed for Ubuntu Linux and a Bash shell,')
# print('or macOS with developer tools installed and possibly additional Homebrew')
# print('tools. If you are not clear yet what these things are, then you need to')
# print('take another introductory course before working on this assignment. The')
# print('University of Illinois offers some intro courses on Coursera that will help')
# print('you understand these things and set up your work environment. (Also, the')
# print('submission scripts assume that you have Python installed as well.)\n')

# # Python2/3 compatibility hacks: ----------------------------

# anchoring_file = 'Application.cpp'

# # Message displayed if compatibility hacks fail
# compat_fail_msg = '\n\nERROR: Python 3 compatibility fix failed.\nPlease try running the script with the "python2" command instead of "python" or "python3".\n\n'
# wrong_dir_msg = '\n\nERROR: Please run this script from the same directory where ' + anchoring_file + ' is.\n\n'

# try:
#   raw_input
# except:
#   # NameError
#   try:
#     raw_input = input
#   except:
#     raise Exception(compat_fail_msg)

# # urllib2 hacks based on suggestions by Ed Schofield.
# # Link: https://python-future.org/compatible_idioms.html?highlight=urllib2
# try:
#   # Python 2 versions
#   from urlparse import urlparse
#   from urllib import urlencode
#   from urllib2 import urlopen, Request, HTTPError
# except ImportError:
#   # Python 3 versions
#   try:
#     from urllib.parse import urlparse, urlencode
#     from urllib.request import urlopen, Request
#     from urllib.error import HTTPError
#   except:
#     raise Exception(compat_fail_msg)

# if not os.path.isfile(anchoring_file):
#   print(wrong_dir_msg)
#   raise Exception(wrong_dir_msg)
# else:
#   print('Found file: ' + anchoring_file)

# # End of compatibility hacks ---------------------------

# """"""""""""""""""""
# """"""""""""""""""""
# class NullDevice:
#   def write(self, s):
#     pass

# def submit():   
#   print('==\n== [sandbox] Submitting Solutions \n==')
  
#   (login, password) = loginPrompt()
#   if not login:
#     print('!! Submission Cancelled')
#     return

  
#   script_process = subprocess.Popen(['bash', 'run.sh', str(0)])
#   output = script_process.communicate()[0]
#   return_code = script_process.returncode
#   if return_code is not 0:
#     raise Exception('ERROR: Build script failed during compilation. See error messages above.')
#   submissions = [source(i) for i in range(3)]
#   submitSolution(login, password, submissions)
  


# # =========================== LOGIN HELPERS - NO NEED TO CONFIGURE THIS =======================================

# def loginPrompt():
#   """Prompt the user for login credentials. Returns a tuple (login, password)."""
#   (login, password) = basicPrompt()
#   return login, password


# def basicPrompt():
#   """Prompt the user for login credentials. Returns a tuple (login, password)."""
#   login = raw_input('Login (Email address): ')
#   print('To validate your submission, we need your submission token.\nThis is the single-use key you can generate on the Coursera instructions page for this assignment.\nThis is NOT your own Coursera account password!')
#   password = raw_input('Submission token: ')
#   return login, password

# def partPrompt():
#   print('Hello! These are the assignment parts that you can submit:')
#   counter = 0
#   for part in partFriendlyNames:
#     counter += 1
#     print(str(counter) + ') ' + partFriendlyNames[counter - 1])
#   partIdx = int(raw_input('Please enter which part you want to submit (1-' + str(counter) + '): ')) - 1
#   return (partIdx, partIds[partIdx])


# def submit_url():
#   """Returns the submission url."""
#   return "https://www.coursera.org/api/onDemandProgrammingScriptSubmissions.v1"

# def submitSolution(email_address,password, submissions):
#   """Submits a solution to the server. Returns (result, string)."""
  
#   values = {
#       "assignmentKey": akey,  \
#       "submitterEmail": email_address, \
#       "secret": password, \
#       "parts": {
#           partIds[0]: {
#               "output": submissions[0]
#           },
#           partIds[1]: {
#               "output": submissions[1]
#           },
#           partIds[2]: {
#               "output": submissions[2]
#           }
#       }
#   }
#   url = submit_url()
#   # (Compatibility update) Need to encode as utf-8 to get bytes for Python3:
#   data = json.dumps(values).encode('utf-8')
#   req = Request(url)
#   req.add_header('Content-Type', 'application/json')
#   req.add_header('Cache-Control', 'no-cache')
#   response = urlopen(req, data)
#   return

# ## This collects the source code (just for logging purposes) 
# def source(partIdx):
#   # open the file, get all lines
#   f = open("dbg.%d.log" % partIdx)
#   src = f.read() 
#   f.close()
#   #print src
#   return src


# def cleanup():
#     for i in range(3):
#         try:
#             os.remove("dbg.%s.log" % i)
#         except:
#             pass


# akey = 'Mj8OkgI-EeaTLQonT2FRpw'
# # the "Identifier" you used when creating the part
# partIds = ['b9m9h', 'MxUat', '8ATm3']
# # used to generate readable run-time information for students
# partFriendlyNames = ['Single Failure', 'Multiple Failure', 'Message Drop Single Failure'] 

# try:
#   submit()
#   print('\n\nSUBMISSION FINISHED!\nYou can check your grade on Coursera.\n\n');
# except HTTPError:
#   print('ERROR:\nSubmission authorization failed. Please check that your submission token is valid.')
#   print('You can generate a new submission token on the Coursera instructions page\nfor this assignment.')

# cleanup()


import httpx
import os
import logging
import asyncio
import subprocess

logger = logging.getLogger("job-system")

SUBMIT_URL = "https://www.coursera.org/api/onDemandProgrammingScriptSubmissions.v1"

akey = 'Mj8OkgI-EeaTLQonT2FRpw'
partIds = ['b9m9h', 'MxUat', '8ATm3']


# ================= RUN SCRIPT =================

def run_script(job_dir: str, src_dir: str):
    process = subprocess.Popen(
        ['bash', 'run.sh', job_dir, src_dir],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout, stderr = process.communicate()

    if process.returncode != 0:
        logger.error(f"[RUN.SH ERROR]\n{stderr.decode()}")
        raise Exception("Build/Run failed")

    logger.info(f"[RUN.SH OUTPUT]\n{stdout.decode()}")


# ================= READ OUTPUT =================

def read_source(job_dir, partIdx):
    path = f"{job_dir}/dbg.{partIdx}.log"

    if not os.path.exists(path):
        raise Exception(f"Missing output file: {path}")

    with open(path) as f:
        return f.read()


# ================= MAIN ENTRY =================

async def submit(email: str, token: str, job_dir: str, src_dir: str):
    try:
        logger.info("[SUBMIT] Running grader script")

        # run grader in thread (non-blocking)
        await asyncio.to_thread(run_script, job_dir, src_dir)

        logger.info("[SUBMIT] Reading outputs")

        submissions = [read_source(job_dir, i) for i in range(3)]

        logger.info("[SUBMIT] Sending to Coursera")

        result = await send_submission(email, token, submissions)

        return result

    except Exception as e:
        logger.error(f"[SUBMIT ERROR] {str(e)}")
        return {"success": False, "error": str(e)}


# ================= SEND TO COURSERA =================

async def send_submission(email, token, submissions):
    payload = {
        "assignmentKey": akey,
        "submitterEmail": email,
        "secret": token,
        "parts": {
            partIds[i]: {"output": submissions[i]} for i in range(3)
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            SUBMIT_URL,
            json=payload,
            headers=headers
        )

    try:
        data = response.json()
        logger.info(f"[COURSERA RESPONSE] {data}")
    except Exception:
        logger.error("[COURSERA] Invalid JSON response")
        return {"success": False, "error": "Invalid response"}

    if "errorCode" in data or "error" in data:
        logger.error(f"[COURSERA ERROR] {data}")
        return {
            "success": False,
            "error": data.get("message") or data.get("error") or "Submission failed"
        }

    logger.info("[COURSERA] Submission success")
    return {"success": True, "data": data}