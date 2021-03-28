#!/bin/bash
# This script do some fixup to Gemini (.gmi or .gemini) file and Gopher files
# (gophermap) to rebase absolute links (starting with '/') to host base folder.
#
# In addition, Some Gopher servers require gophermap to fully comply with 
# RFC 1436 while others are more forgiven. This scrip process relaxed 
# gophermaps to convert them to strict RFC 1436 (forcing each line to have 
# three tabs and five sections - by inserting the host and port where missing)
#
# Execute it with --help for usage information
#
# Examples:
#
# Rebase a Gemini capsule:
#          ./fixup.sh -ge 'dir1/dir2' public-gg/gemini
#
# Rebase a Gopher hole:
#          ./fixup.sh -go 'dir1/dir2' -h my-server.com  public-gg/gopher
#
# Add the host and port to a Gopher hole
#          ./fixup.sh -h my-server.com  public-gg/gopher
#
# Clean-up (remove *.save files):
#          ./fixup.sh -clean public-gg
#
###############################################################################

# Default arguments:
gebase=""
gobase=""
host="null.host"
port="70"
debug=""
path=""

echo "Start $(date)"

## Used to clean-up the backup files created during the operation of this scrip
function clean_up ()
{
    echo "cleaning up ${path}"
    find "${path}" -type f -iname "*.save" -exec rm {} \;
    find "${path}" -type f -iname "*~" -exec rm {} \;
    exit
}

## Description of the arguments
function arguments ()
{
    echo "Usage: $0 [flags] <path>"
    echo
    echo " -ge, --gemini <base>  Add <base> to links stating with '/'"
    echo " -go, --gopher <base>  Add <base> to links stating with '/'"
    echo " -h,  --host   <host>  Gopher host name (default to 'null.host')"
    echo " -p,  --port   <port>  Gopher port number (default to '70')"
    echo " -d,  --debug          Keep a copy .save of each modified file"
    echo " -c,  --clean          Cleans the <path> of .save files"
    echo " -h,  --help    Print this message"
    exit
}

## Script starts by processing the arguments
while [ ! -z "$1" ]
do
    case "$1" in
        --gemini|-ge)
            shift
            gebase="$1"
            shift
            ;;
        --gopher|-go)
            shift
            gobase="$1"
            shift
            ;;
        --host|-h)
            shift
            host="$1"
            shift
            ;;
        --port|-p)
            shift
            port="$1"
            shift
            ;;
        --debug|-d)
            shift
            debug="-v inplace::suffix=.save"
            ;;
        --clean|-c)
            shift
            clean="TRUE"
            ;;
        --help|-h)
            arguments
            ;;
        *)
            break
    esac
done
path="$1"

## The <path> argument is mandatory
if [ -z "${path}" ]; then
    echo "missing <path>"
    arguments
    exit
fi

## Clean-up will work and exit the script
if [ ! -z "${clean}" ]; then
    clean_up
fi

## The only valid operation for Gemini is to rebase
if [ ! -z "${gebase}" ]; then
    echo "Processing Gemini capsule at ${path}"
    find "${path}" -type f -iname "*.gmi" -exec gawk -i inplace -v base="${gebase}" \
        -v inplace::suffix=.save '
            /^[ \t]*=>[ \t]*\// {gsub(/^[ \t]*=>[ \t]*\//, "=> /" base "/")}
            { print}
            ' {} \;
fi

## We can process gophermaps without gobase:
echo "Processing Gopher hole at ${path}"
find "${path}" -type f -iname "gophermap" -exec gawk -i inplace -v base="${gobase}" \
    -v inplace::suffix=.save  -v host="${host}" -v port="${port}"  '
        BEGIN {FS="\t"}
        {gsub("\r|\n","")
        if (NF == 1) 
            print "i" $1 "\t/\t" host "\t" port 
        else if (NF == 2) {
            gsub("^/","/" base "/",$2)
            print $1 "\t" $2 "\t" host "\t" port}
        else if (NF == 3) 
            print $1 "\t" $2 "\t" $3 "\t" port 
        else 
            print}
        ' {} \;

echo "Done $(date)"
