#!/usr/bin/python3 -u

""" Convert a static web site to and enbedded system

This script can be used to encode an static web site (for example one generated
by Hugo (https://gohugo.io/) to an embedded site to be hosted in a microcontroller
"""

import os
import re
import io
import sys
import getopt
import random
import urllib
import inspect
import datetime
import mimetypes
import subprocess

verbose = False
keepTmpFiles = False

def vbprint(*args, **kwargs):
    if verbose:
        print(*args, **kwargs)


def error(*args, **kwargs):
    if verbose:
        print("ERROR [",os.path.basename(sys.argv[0]),":",inspect.currentframe().f_back.f_lineno,"]: ",
                *args, **kwargs, sep="", file = sys.stderr)
    else:
        print("ERROR: ", *args, **kwargs, sep="", file = sys.stderr)


def warn(*args, **kwargs):
    if verbose:
        print("WARNING [",os.path.basename(sys.argv[0]),":",inspect.currentframe().f_back.f_lineno,"]: ",
                *args, **kwargs, sep="", file = sys.stderr)
    else:
        print("WARNING: ", *args, **kwargs, sep="", file = sys.stderr)

def delete_file(name, clean = True):
    if keepTmpFiles:
        return
    try:
        path = os.path.dirname(name)
        os.remove(name)

        if clean:
            while len(os.listdir(path)) == 0:
                base = os.path.dirname(path)
                os.rmdir(path)
                path = base

    except OSError as e:
        warn(e, "deleting ",name)


def clean_dir(folder):
    """Clean a directory or folder name by removing special characters

    Parameters
    ----------
    folder: str
        directory or folder name

    Returns
    -------
    str
    """

    out = folder.split(os.sep)
    while('' in out):
        out.remove('')
    ret = []    
    for e in out:
        ret.append(re.sub(r'[^0-9a-zA-Z-]+', '-', e))

    rtrn = ""
    if folder and folder[0] == os.sep:
        rtrn = os.sep + os.sep.join(ret)
    elif folder:
        rtrn = os.sep.join(ret)

    return rtrn


def clone_file(src, dst):
    """Copy the src file to the dst file treating them as binary files

    Parameters
    ----------
    src : str
        Source full file name
    dst : str
        Destination full file name

    Returns
    -------
    Nothing
    """

    vbprint("CLONE:",src,"->",dst)
    try:
        dstFolder = os.path.dirname(dst)
        if not os.path.exists(dstFolder):
            os.makedirs(dstFolder)

        with open(src, 'rb') as flSrc:
            with open(dst, 'wb') as flDst:
                flDst.write(flSrc.read())

    except OSError as e:
        error(e, " while processing files", src,"=>",dst)


def justify (txt):
    missing = 70 - len(txt)
    leading = 0
    if missing == 0:
        return txt
    while txt[leading] == ' ':
        txt = txt[1:]
        leading += 1
    words = txt.split()
    blanks = re.findall(r'\s+', txt.strip())
    nblanks = len(words) - 1
    if nblanks != len(blanks):
        error("INTERNAL Error mistmatch of spaces (nblanks:",nblanks," len(blanks):",len(blanks),
                "\nwords:",words,"\nblanks:",blanks,"\nTXT:|",txt,"|")
    if nblanks < 1:
        warn("Line too long without a blank (",nblanks, ")=>[",words,"]")

    #print("JUSTIFY: missing=",missing,"blanks=",nblanks)
    while (missing >= nblanks) and (nblanks > 0):
        for i in range(len(blanks)):
            blanks[i] += ' '
        missing -= nblanks

    flags = [True] * (nblanks)

    while (missing > 0) and (nblanks > 0):
        i = random.randint(0,nblanks-1)
        if flags[i]:
            blanks[i] += ' '
            flags[i] = False
            missing -= 1

    text = ''
    if leading > 0:
        text = ' ' * leading
    for i in range(len(blanks)):
        text += words[i] + blanks[i]
    text += words[-1]
    #print("     1234567890123456789012345678901234567890123456789012345678901234567890\nTXT:", txt,"\n    ",text)
    return text



def gopher_text(txt, prefix):
    lines = []

    # Process headings
    isHeader = False
    if re.search(r"^\s*#+\s",txt):
        txt = re.sub(r"^\s*#+\s",'',txt)
        lines.append(prefix)
        lines.append(prefix)
        isHeader = True

    if len(txt) == 0:
        lines.append(prefix)

    # Now break long lines into chunks of around 70 chars
    i = 0
    n = 70 # Magic gopher number
    firstTime = True
    while i < len(txt):
        if i + n < len(txt):
            t = i + n
            while t > i and txt[t] != ' ':
                t -= 1
            if t == i:
                t = i + n
            if firstTime:
                lines.append(prefix + justify(txt[i:t].rstrip()))
            else:
                lines.append(prefix + justify(txt[i:t].strip()))
            i = t
        else:
            if firstTime:
                lines.append(prefix + txt[i:len(txt)].rstrip())
            else:
                lines.append(prefix + txt[i:len(txt)].strip())
            i += n
        if firstTime and isHeader:
            lines.append(prefix)
        firstTime = False
    return lines


def extract_arg(line):
    arg = {}
    line = line.rstrip('\r\n')
    if line and (line[0:6] == '[[[=> ') and (line[-5:] == '<=]]]'):
        line = line[6:-5].replace('<no value>','false')
    else:
        return arg
    pairs = line.split(',')
    for pair in pairs:
        single = pair.split(':')
        if len(single) == 2:
            arg[single[0]] = True if single[1] == 'true' else False if single[1] == 'false' else single[1]
    return arg


def clean_markdown(line):
    # strip bold and italic enclosed in asterisk (*)
    emphasis = re.findall(r'\*+[^\*]+\*+',line)
    for item in emphasis:
        new = item
        while (new[0] == '*') and (new[-1] == '*'):
            new = new[1:-1]
        line = line.replace(item, new)
    # strip bold and italic enclosed in underscore (_)
    emphasis = re.findall(r'_+[^_]+_+',line)
    for item in emphasis:
        new = item
        while (new[0] == '_') and (new[-1] == '_'):
            new = new[1:-1]
        line = line.replace(item, new)
    # strip code enclosed in one backticks (`)
    emphasis = re.findall(r"[^`]`[^`]+`[^`]",line)
    for item in emphasis:
        line = line.replace(item, item[1:-1])
    # strip code enclosed in two backticks (``)
    emphasis = re.findall(r"``.+``",line) # Will not work in all cases
    for item in emphasis:
        line = line.replace(item, item[2:-2])
    return line


def extract_links(line, pageLinks):
    lineLinks = re.findall(r'!?\[[^\]]*\]\([^\)]*\)|<[^<]+[@:][^<]+>',line)
    for link in lineLinks:
        if link[0] == '<' and link[-1] == '>':
            link = '[' + link[1:-1] + '](' + link[1:-1] + ')'
        link = re.sub(r'\s+"[^"]+"\s*\)',')',link)
        if not (link in pageLinks):
            pageLinks[link] = len(pageLinks) + 1
        ref = link.split('](')
        if len(ref) != 2:
            error(" Invalid link '",src,"', line ",count,":",link);
        if ref[0][0] == '!':
            cite = ref[0][2:] + ' [' + str(pageLinks[link]) + ']'
        else:
            cite = ref[0][1:] + ' [' + str(pageLinks[link]) + ']'
        line = line.replace(link,cite)
    return line, pageLinks


def one_line_link(line):
    single = {}
    if re.search(r'^i?\s*!?\[[^\]]*\]\([^\)]*\)\s*$|^i?\s*<[^<]+[@:][^<]+>\s*$',line):
        single['hint'] = 'I' if re.search(r'^i?\s*!\[',line) else 'h'
        link = line[1:].strip(' <![)>\t') if line[0] == 'i' else line.strip(' <![)>\t')
        link = re.sub(r'\s+"[^"]+"\s*\)',')',link)
        ref = link.split('](')
        single['uri'] = ref[0]
        single['label'] = ref[0]
        if len(ref) == 2:
            single['uri'] = ref[1]
        elif len(ref) > 2:
            error(" Invalid link [",link,"]");
    return single


def convert_gopher(src, dst, arPath, arLast):

    def item_type(uri, hint):
        item = hint
        if uri[0] == '/':
            mime = mimetypes.MimeTypes().guess_type(uri)[0]
            if not mime:
                return '1'
            mm = mime.split('/')
            if not mime:
                item = '1' # Directory
            elif mime == 'image/gif':
                item = 'g' # GIF graphic
            elif mime == 'text/html':
                item = 'h' # HTML file
            elif mm[0] == 'text':
                item = '0' # Plain text
            elif (mm[0] == 'application') or (mm[0] == 'video'):
                item = '9' # Binary (including pdf)
            elif mm[0] == 'image':
                item = 'I' # grafic files other than GIF
            elif mm[0] == 'audio':
                item = 's' # Sound file
            else:
                item = '9' # default to Binary
        return item


    # Notes on gophermap syntax (https://tools.ietf.org/html/rfc1436): 
    # 1- gopher text lines keep to 70 chars
    # 2- lines must end with <CR><LF> (meaning '\r\n')
    vbprint("CONVERT:",src,"->",dst)
    replacePage = False
    try:
        count = 0
        countOtherLinks = 0
        isFenced = False
        pageLinks = {}
        lineEnd = '\r\n'
        arg = {}
        filler = ""

        flSrc = open(src, 'rt')
        flDst = open(dst, 'wt')

        def print_references(prefix):
            if len(pageLinks) == 0:
                if countOtherLinks  == 0:
                    warn("No links in '",src,"', it should be better be a txt file (instead of a gophermap)")
                return
            flDst.write(prefix + '\t' + filler + lineEnd + prefix + 'References:\t' + filler + lineEnd)
            for key, value in sorted(pageLinks.items(), key=lambda item: item[1]):
                ref = key.split('](')
                hint = 'I' if ref[0][0] == '!' else 'h'
                label = ref[0][2:] if ref[0][0] == '!' else ref[0][1:]
                uri = ref[1][:-1]
                lineItem = item_type(uri, hint)
                if lineItem == 'h':
                    uri = 'URL:' + uri
                flDst.write(lineItem + '  [' + str(value) + '] ' + label + '\t' + uri + filler + lineEnd)


        while True:
            line = flSrc.readline()
            if not line:
                break
            if count == 0:
                arg = extract_arg(line)
                if arg:
                    continue
            count += 1
            if arg and arg['copyPage']:
                replacePage = True
                break
            if arg and arg['keepRaw']:
                flDst.write(line)
                continue
            line = line.rstrip('\r\n') # remove trailing <CR> and/or <LF>
            if re.search(r"^i?\s*```",line): #toggle fenced code
                isFenced  = not isFenced
                continue
            if isFenced:
                if len(line.split('\t',1)[0]) > 70:
                    warn("Fenced line too long (exceed 70 chars by ",len(line.split('\t',1)[0])-70," chars) in '",src,"', line",count)
                flDst.write(line + lineEnd)
                continue
            if not line:
                continue
            # Strict gopher: lines are composed of five parts:
            # item: one character describing the item type
            # text: user visible string or label
            # selector: often a path, uri or other file selector
            # domain: the domain name of the host containing the selector
            # port: the port used by the domain
            #
            #line is: <item><text>[<TAB><selector>[<TAB><domain>[<TAB><port>]]]<CR><LF>
            #
            line = line.replace('gophermap.txt','gophermap')
            linePart = line.split('\t')
            nLineParts = len(linePart)
            if nLineParts == 4:
                filler = ""
            elif (nLineParts <= 2) and arg and arg['fullLine']:
                filler = '\t' + arg['host'] + '\t' + arg['port']
            elif nLineParts > 4:
                error(" Extra tabs in '",src,"', line ",count,":",linePart);

            if line.strip() == '[[[=> references <=]]]':
                print_references('i' if arg and (arg['textChar'] or arg['fullLine']) else '')
                continue

            # need to extract and replace links [text](link)
            # Links alone in a single line shoul be placed in the same line
            single = one_line_link(line)
            if single:
                flDst.write(item_type(single['uri'], single['hint']) + '  ' + single['label'] + '\t' + single['uri'] + filler + lineEnd)
                continue

            # Links embeded in the text of the line must be collected for late placement
            linePart[0], pageLinks = extract_links(linePart[0], pageLinks)

            linePart[0] = clean_markdown(linePart[0])
            if linePart[0][0] in ['0','1','4','5','6','9','g','I','h','s']:
                countOtherLinks += 1
            if linePart[0][0] == 'i':
                lines = gopher_text(linePart[0][1:], 'i' if arg and (arg['textChar'] or arg['fullLine']) else '')
                for l in lines:
                    if nLineParts > 3:
                        lne = l + '\t' + linePart[1] + '\t' + linePart[2]+ '\t' + linePart[3]
                    elif nLineParts > 2:
                        lne = l + '\t' + linePart[1] + '\t' + linePart[2]
                    elif nLineParts > 1:
                        lne = l + '\t' + linePart[1]
                    else:
                        lne = l
                    flDst.write(lne + filler + lineEnd)
                continue
            flDst.write(line + filler + lineEnd)


    except OSError as e:
        error(e, " while processing files", src,"=>",dst)

    flSrc.close()
    flDst.close()
    delete_file(src)
    if replacePage:
        delete_file(dst, False)
        clone_file(dst.replace(arPath, arLast, 1), dst)


def convert_gemini(src, dst, arPath, arLast):

    vbprint("CONVERT:",src,"->",dst)
    replacePage = False
    try:
        count = 0
        isFenced = False
        pageLinks = {}

        flSrc = open(src, 'rt')
        flDst = open(dst, 'wt')

        def print_references():
            if len(pageLinks) == 0:
                return
            flDst.write('\nReferences:\n')
            for key, value in sorted(pageLinks.items(), key=lambda item: item[1]):
                ref = key.split('](')
                if ref[0][0] == '!':
                    flDst.write('=> ' + urllib.parse.quote(ref[1][:-1],':/?=+&') + '  [' + str(value) + '] ' + ref[0][2:] + '\n')
                else:
                    flDst.write('=> ' + urllib.parse.quote(ref[1][:-1],':/?=+&') + '  [' + str(value) + '] ' + ref[0][1:] + '\n')
            flDst.write('\n')

        while True:
            line = flSrc.readline()
            if not line:
                break
            if count == 0:
                arg = extract_arg(line)
                if arg:
                    continue
            count += 1
            if arg and arg['copyPage']:
                replacePage = True
                break
            if arg and arg['keepRaw']:
                flDst.write(line)
                continue
            if re.search(r"^\s*```",line): #toggle fenced code
                isFenced  = not isFenced
            if isFenced:
                flDst.write(clean_markdown(line))
                continue
            # need to extract and replace links [text]()
            # Links alone in a single line shoul be placed in the same line
            single = one_line_link(line.strip('\r\n'))
            if single:
                #flDst.write('=> ' + single['uri'] + '   ' + single['label'] + '\n')
                flDst.write('=> ' + urllib.parse.quote(single['uri'],':/?=+&') + '   ' + single['label'] + '\n')
                continue

            # Links embeded in the text of the line must be collected for late placement
            line, pageLinks = extract_links(line, pageLinks)

            if line.strip() == '[[[=> references <=]]]':
                print_references()
                continue

            flDst.write(clean_markdown(line))


    except OSError as e:
        error(e, " while processing files", src,"=>",dst)

    flSrc.close()
    flDst.close()
    delete_file(src)
    if replacePage:
        delete_file(dst, False)
        clone_file(dst.replace(arPath, arLast, 1), dst)


def traverse_gemini(arGemini, arPath, arLast):
 
    count = 0
 
    print("\nGemini phase -- preparing capsule\n")

    # Get a list of all files in the gemini capsule
    for rootDir, subdirs, filenames in os.walk(arGemini):
        # process each file
        for filename in filenames:
            try:
                # sourceName is the complete file name including the folder structure (full path)
                sourceName = os.path.join(rootDir, filename)
                # name is the file name without path or extension
                # ext is the file extension
                name, ext = os.path.splitext(filename)

                vbprint("CAPSULE: rootDir='",rootDir,"', subDirs=",subdirs,", filename='",filename,"'", sep="")

                if ext.lower() == ".gmi":
                    count += 1
                    base = os.path.basename(rootDir)
                    if (base.lower() == "gemini") or not base:
                        base = "index"
                    os.rename(sourceName, sourceName + "-old")
                    folder = os.path.dirname(rootDir)
                    if folder == arPath:
                        convert_gemini(sourceName + "-old", os.path.join(rootDir, base + ".gmi"), arPath, arLast)
                    else:
                        convert_gemini(sourceName + "-old", os.path.join(folder, base + ".gmi"), arPath, arLast)

            except OSError as e:
                error(e," while processing gemini file", filename)

    print("Number of gemini capsule files", count)


def traverse_gopher(arGopher, arPath, arLast):
 
    count = 0
 
    print("\nGopher phase -- digging hole\n")

    # Get a list of all files in the gopher hole
    for rootDir, subdirs, filenames in os.walk(arGopher):
        # process each file
        for filename in filenames:
            try:
                # sourceName is the complete file name including the folder structure (full path)
                sourceName = os.path.join(rootDir, filename)

                vbprint("HOLE: rootDir='",rootDir,"', subDirs=",subdirs,", filename='",filename,"'", sep="")

                if filename.lower() == "gophermap.txt":
                    count += 1
                    convert_gopher(sourceName, os.path.join(rootDir, "gophermap"), arPath, arLast)

            except OSError as e:
                error(e," while processing gopher file", filename)

    print("Number of gopher hole files", count)


def traverse_site(arPath, arGopher, typeGopher, arGemini, typeGemini):
 
    count = 0
    lenArGopher = len(arGopher)
    lenArGemini = len(arGemini)
    oldFiles = []

    print("Prepare phase\n")
 
    # Get a list of all files in the site
    for rootDir, subdirs, filenames in os.walk(arPath):
        try:
            for filename in filenames:
                vbprint("SOURCE: rootDir='",rootDir,"', subDirs=",subdirs,", filename='",filename,"'", sep="")

                ## A) Prepare to process the file
                # sourceName is the complete file name including the directory structure (full path)
                sourceName = os.path.join(rootDir, filename)

                # name is the file name without path or extension
                # ext is the file extension
                name, ext = os.path.splitext(filename)
                base = os.path.basename(rootDir)

                ## B) Files in the right directory
                ## Process gopher or gemini files that are in the right directory structure
                ## Meaning files that are under the correct arGopher or arGemini directory
                if (((len(rootDir) >= lenArGopher) and (rootDir[0:lenArGopher] == arGopher))
                        or ((len(rootDir) >= lenArGemini) and (rootDir[0:lenArGemini] == arGemini))):
                    vbprint("=>",rootDir, ":", [arGopher, arGemini])

                    continue

                ## C) Files in the wrong directory
                ## process file that need to be clone into the arGopher or arGemini directory structure 
                count += 1
                # root is the original path without the site directory arPath
                root = clean_dir(rootDir.replace(arPath + os.sep,"",1))
                root = '' if root == rootDir else root

                if base in ["gopher", "gemini"]:
                    root = clean_dir(root.replace(os.sep + base,"",1))

                if base == "gopher" and typeGopher:
                    clone_file(sourceName,os.path.join(arGopher,root,filename))
                    oldFiles.append(sourceName)
                if base == "gemini" and typeGemini:
                    clone_file(sourceName,os.path.join(arGemini,root,filename))
                    oldFiles.append(sourceName)

                ## D) Files that come from the Hugo's static directory
                if not (base in ["gopher", "gemini"]):
                    if typeGopher:
                        clone_file(sourceName,os.path.join(arGopher,root,filename))
                    if typeGemini:
                        clone_file(sourceName,os.path.join(arGemini,root,filename))
                    oldFiles.append(sourceName)

        except OSError as e:
            error(e," while processing file", filename)

    for fl in oldFiles:
        delete_file(fl)
    print("Number of cloned files", count)


def fix_hugo_nested_paths(arPath, arGemini, arGopher):
    #
    # Sometimes hugo generates nested paths
    # It happens in "test-hugo-theme-console", 
    #    where "public-gg/gemini/gemini" and "public-gg/gopher/gemini" are generated
    # So, this is a kludge to fix that hugo behaviour
    geminiPath = arGemini.replace(arPath + os.sep, "", 1)
    gopherPath = arGopher.replace(arPath + os.sep, "", 1)
    badPath = [os.path.join(arPath, geminiPath, geminiPath), 
               os.path.join(arPath, geminiPath, gopherPath), 
               os.path.join(arPath, gopherPath, geminiPath), 
               os.path.join(arPath, gopherPath, gopherPath)] 
    for path in badPath:
        if not os.path.isdir(path):
            continue
        vbprint("Fixing hugo generated nested path", path)
        if path.endswith(os.sep + geminiPath):
            goodPath = path[:-len(os.sep + geminiPath)]
        elif path.endswith(os.sep + gopherPath):
            goodPath = path[:-len(os.sep + gopherPath)]
        isGemini = path.startswith(arGemini)
        for rootDir, subdirs, filenames in os.walk(path):
            try:
                for filename in filenames:
                    sourceName = os.path.join(rootDir, filename)
                    if isGemini:
                        targetName = os.path.join(os.path.dirname(rootDir), filename).replace(path, goodPath, 1)
                    else:
                        targetName = sourceName.replace(path, goodPath, 1)
                    clone_file(sourceName, targetName)
                    delete_file(sourceName)

            except OSError as e:
                error(e," while processing file", filename)


def execHugo(arNoHugo, arPath, arConfig, arEmpty):
    hugo = ['hugo', '--config', arConfig, '--destination', arPath, '--layoutDir', arEmpty, '--disableKinds', 'sitemap']
    cmd = ' '.join(hugo)
    if arNoHugo:
        print("Skipping hugo execution (suggest:",cmd,")")
        return
    else:
        print("Executing:",cmd)
    res = subprocess.run(hugo)
    if res.returncode != 0:
        error("Hugo execution failed with", res.returncode)
        sys.exit(2)


def arguments() :
    print("Usage:\n ",os.path.basename(sys.argv[0])," [flags]\n\nFlags:")
    print("   -p, --path    <path>  Path of the site to be converted (default to public-gg)")
    print("   -g, --gopher  <path>  Gopher output folder (default to public-gg/gopher)")
    print("   -G, --gemini  <path>  Gemini output folder (default to public-gg/gemini)")
    print("   -e, --empty   <path>  Path of empty folder (default to layouts-gg)")
    print("   -l, --last    <path>  Path for last build folder (default to public-gg-sav)")
    print("   -c, --config  <file>  Name of the hugo config file (default to config-gg.toml)")
    print("   -t, --type    <type>  type of output to be generated (default to all)")
    print("                         <type> can be:")
    print("                                all      Generate both gopher and gemini sites")
    print("                                gopher   Generate only the gopher hole")
    print("                                gemini   Generate only the gemini capsule")
    print("   -k, --keep            Keep processed temporary files for debugging purposes")
    print("   -n, --no-hugo         Do not run  hugo. Remember to run hugo before this.")
    print("   -h, --help            Prints this help")
    print("   -v, --verbose         Produces verbose stdout ourput")
    sys.exit(2)


def main(argv):
   nargs = 0

   # arguments:
   arConfig = "config-gg.toml"
   arPath   = "public-gg"
   arGopher = "public-gg" + os.sep + "gopher"
   arGemini = "public-gg" + os.sep + "gemini"
   arLast   = "public-gg-sav"
   arEmpty  = "layouts-gg"
   typeGopher = False
   typeGemini = False
   arNoHugo = False
   arType = "all"

   try:
       opts, args = getopt.getopt(argv,"he:p:l:c:g:G:vt:kn",
               ["help","empty=","path=","last=","config=","gopher=","gemini=","verbose","type=","keep","no-hugo"])
   except getopt.GetoptError as e:
      error(e)
      arguments()
   for opt, arg in opts:
      nargs += 1
      if (opt in ("-h","--help")) or (len(sys.argv) == 1):
         arguments()
      elif opt in ("-l", "--last"):
         arLast = arg
      elif opt in ("-p", "--path"):
         arPath = arg
      elif opt in ("-e", "--empty"):
         arEmpty = arg
      elif opt in ("-c", "--config"):
         arConfig = arg
      elif opt in ("-g", "--gopher"):
         arGopher = clean_dir(arg)
      elif opt in ("-G", "--gemini"):
         arGemini = clean_dir(arg)
      elif opt in ("-t", "--type"):
          arType = arg
      elif opt in ("-v", "--verbose"):
          global verbose
          verbose = True
      elif opt in ("-n", "--no-hugo"):
          arNoHugo = True
      elif opt in ("-k", "--keep"):
          global keepTmpFiles
          keepTmpFiles = True
      elif opt == "": 
          error("Invalid argument")
          arguments()

   if not (arType in ("all", "gopher", "gemini")):
      error("Invalid type ", arType)
      arguments()

   print("Proceeding as follows:\n    Input folder: ",arPath)
   if arType in ("all", "gopher"):
       print("    Gopher folder:",arGopher)
       typeGopher = True
   if arType in ("all", "gemini"):
       print("    Gemini folder:",arGemini)
       typeGemini = True
   print("    Config file:  ", arConfig, "\n    Last output:  ", arLast,"\n")

   execHugo(arNoHugo, arPath, arConfig, arEmpty)
   traverse_site(arPath, arGopher, typeGopher, arGemini, typeGemini)
   if typeGopher:
       traverse_gopher(arGopher, arPath, arLast)
   if typeGemini:
       traverse_gemini(arGemini, arPath, arLast)

   #### For some unknown reason to me, sometimes hugo generates nested folders as follows:
   ####     public-gg/gemini/gemini/...
   ####     public-gg/gopher/gemini/...
   ####     public-gg/gopher/gopher/...
   ####     public-gg/gemini/gopher/...
   #### Don't understand why hugo do that, but it needs to be fixed, so
   fix_hugo_nested_paths(arPath, arGemini, arGopher)

   print("done")

if __name__ == "__main__":
   main(sys.argv[1:])

