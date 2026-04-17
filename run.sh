# #!/usr/bin/env bash

# #**********************
# #*
# #* Progam Name: MP1. Membership Protocol.
# #*
# #* Current file: run.sh
# #* About this file: Submission shell script.
# #* 
# #***********************

# # 20191021: Edited by CS Instructional Design staff for compatibility with macOS
# # 20191024: Packaging the needed files directly to remove download dependency,
# #   adding more error checking for the environment setup

# if [ ! -e "Application.cpp" ]; then
#   echo -e '\n\nERROR: This script "run.sh" should be located in the same directory where the Application.cpp file is.\n\n'
#   exit 1
# fi

# if [ ! -e "mp1-regen-data" ]; then
#   echo -e '\n\nERROR: The "mp1-regen-data" file was not found in this directory. Replace it from the files you were given.\n\n'
#   exit 1
# fi

# if [ ! $(which tar) ]; then
#   echo -e '\n\nERROR: Your system needs the "tar" command to be installed first.\n\n'
#   exit 1
# fi

# if [ ! $(which make) ]; then
#   echo -e '\n\nERROR: You do not have the "make" tool installed in your shell environment.\n\n'
#   exit 1
# fi

# if [ ! $(which g++) ]; then
#   echo -e '\n\nERROR: You do not have the "g++" tool installed in your shell environment. You need to install gcc and/or g++ tools first.\n\n'
#   exit 1
# fi

# rm -rf grade-dir # Make sure grade-dir is clean before starting
# rm -f dbg.*.log

# mkdir grade-dir
# cd grade-dir

# cp ../mp1-regen-data mp1-regen-data-tmp.tar
# tar -xf mp1-regen-data-tmp.tar

# cd mp1
# cp ../../MP1Node.* .
# make clean > /dev/null
# make > /dev/null

# if [ ! -e "./Application" ]; then
#   echo -e '\n\nERROR: Compilation was not successful.\nSee error messages by typing: make clean && make\n\n'
#   exit 1
# fi

# ./Application testcases/singlefailure.conf > /dev/null
# cp dbg.log ../../dbg.0.log
# ./Application testcases/multifailure.conf > /dev/null
# cp dbg.log ../../dbg.1.log
# ./Application testcases/msgdropsinglefailure.conf > /dev/null
# cp dbg.log ../../dbg.2.log
# cd ../..
# rm -rf grade-dir



#!/usr/bin/env bash

# ================= INPUT =================
WORKDIR=$1
SRCDIR=$2

LOG_PREFIX="[RUN.SH]"

if [ -z "$WORKDIR" ] || [ -z "$SRCDIR" ]; then
  echo "$LOG_PREFIX ERROR: Usage run.sh <workdir> <srcdir>"
  exit 1
fi

echo "$LOG_PREFIX Starting job in $WORKDIR"

# ================= SETUP =================

mkdir -p "$WORKDIR" || { echo "$LOG_PREFIX ERROR: cannot create workdir"; exit 1; }
cd "$WORKDIR" || { echo "$LOG_PREFIX ERROR: cannot enter workdir"; exit 1; }

rm -f dbg.*.log

# ================= VALIDATION =================

if [ ! -e "$SRCDIR/Application.cpp" ]; then
  echo "$LOG_PREFIX ERROR: Application.cpp not found in src"
  exit 1
fi

if [ ! -e "$SRCDIR/mp1-regen-data" ]; then
  echo "$LOG_PREFIX ERROR: mp1-regen-data missing in src"
  exit 1
fi

# ================= PREPARE =================

echo "$LOG_PREFIX Preparing grader..."

mkdir grade-dir || { echo "$LOG_PREFIX ERROR: cannot create grade-dir"; exit 1; }
cd grade-dir || exit 1

cp "$SRCDIR/mp1-regen-data" mp1-regen-data-tmp.tar || { echo "$LOG_PREFIX ERROR: copy failed"; exit 1; }

tar -xf mp1-regen-data-tmp.tar || { echo "$LOG_PREFIX ERROR: extraction failed"; exit 1; }

cd mp1 || { echo "$LOG_PREFIX ERROR: mp1 folder missing"; exit 1; }

# ================= COPY USER CODE =================

echo "$LOG_PREFIX Copying user code..."

cp "$SRCDIR"/MP1Node.* . || { echo "$LOG_PREFIX ERROR: missing MP1Node files"; exit 1; }

# ================= BUILD =================

echo "$LOG_PREFIX Building..."

make clean > /dev/null 2>&1
make > /dev/null 2>&1 || { echo "$LOG_PREFIX ERROR: build failed"; exit 1; }

if [ ! -e "./Application" ]; then
  echo "$LOG_PREFIX ERROR: build did not produce Application"
  exit 1
fi

# ================= RUN TESTS =================

echo "$LOG_PREFIX Running tests..."

echo "$LOG_PREFIX Test: singlefailure"
./Application testcases/singlefailure.conf || { echo "$LOG_PREFIX ERROR: singlefailure crashed"; exit 1; }
cp dbg.log "$WORKDIR/dbg.0.log"

echo "$LOG_PREFIX Test: multifailure"
./Application testcases/multifailure.conf || { echo "$LOG_PREFIX ERROR: multifailure crashed"; exit 1; }
cp dbg.log "$WORKDIR/dbg.1.log"

echo "$LOG_PREFIX Test: msgdropsinglefailure"
./Application testcases/msgdropsinglefailure.conf || { echo "$LOG_PREFIX ERROR: msgdrop test crashed"; exit 1; }
cp dbg.log "$WORKDIR/dbg.2.log"

# ================= CLEANUP =================

cd "$WORKDIR" || exit 1
rm -rf grade-dir

echo "$LOG_PREFIX Completed successfully ✅"
