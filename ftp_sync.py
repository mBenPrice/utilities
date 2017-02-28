import sys, os, time
from ftplib import FTP, error_perm

DevDirs = [     ("Folder Name",                 r"C:\Local\Location")]
FTPDirs = [   ("Folder Name",                 r"/remote/location")]

#####################################
#
#  Creates global ftp connection with ftp credentials
#  so the ftp variable is available for usage elsewhere.
#
#####################################
def connect_ftp():
    global ftp
    trying = True
    count = 0
    ftp_user = "user"
    ftp_pass = "pass"
    host_addr = "IP"
    port_num = 21    
    
    while trying:
        trying = False
        try:
            ftp = FTP(host_addr)
            ftp.set_debuglevel(0) # change 0 to 1 for verbose
            ftp.connect(host_addr, port_num)
            ftp.set_pasv(False) # necessary for some FTP server servers
            ftp.getwelcome()
            ftp.login(ftp_user, ftp_pass)
        except:
            count += 1
            trying = True
            if count > 5:
                print "Connection dropped.  Waiting a few before attempting again."
                time.sleep(3 * 60)
                count = 0
            print "Retrying FTP connect..."


#####################################
#
#  Because FTP transfers tend to fail periodically, ftp_listing 
#  provides a reliable method of getting a directing listing (nlst).
#  Upon failure, ftp_listing will reconnect, change to the 
#  appropriate directory, try again...
#
#####################################
def ftp_listing(r_dir):
    count = 0
    trying = True
    
    while trying:
        trying = False
        try:
            ftp.cwd(r_dir)
            g_list = ftp.nlst()
        except:
            trying = True
            count += 1
            if count > 5:
                print "Connection dropped.  Waiting a few before attempting again."
                time.sleep(3 * 60)
                count = 0
            print "Reconnecting to remote server..."
            connect_ftp()
            ftp.cwd(r_dir)
            print "Retrying nlst..."
    
    return g_list


#####################################
#
#  Because FTP transfers tend to fail periodically, ftp_up provides a
#  reliable method of uploading a file until completion.
#  Upon failure, ftp_up will reconnect, change to the appropriate
#  directory, try again...
#
#####################################
def ftp_up(l_file, l_dir, r_dir):
    logg
    count = 0
    os.chdir(l_dir)
    ftp.cwd(r_dir)
    uploading = True
    u_time = time.localtime(time.time())
    print "Writing %s\n\tsize %d at %d %d/%d %02d%02d" % \
        (l_file, os.path.getsize(l_file),
         u_time[0], u_time[1], u_time[2], u_time[3], u_time[4])
    logg += "Writing %s\n\tsize %d at %d %d/%d %02d%02d\n" % \
        (l_file, os.path.getsize(l_file),
         u_time[0], u_time[1], u_time[2], u_time[3], u_time[4])
    while uploading:
        uploading = False
        try: ftp.delete(l_file + ".ihs") # Get rid of any backup.
        except: pass
        
        try:
            # Store file with temporary .ihs file name, which will
            # be detected as a partial upload if the transfer cuts out
            ftp.storbinary("STOR " + l_file + ".ihs", open(l_file, 'rb'))
        except:
            count += 1
            uploading = True
            if count > 5:
                print "Connection dropped.  Waiting a few before attempting again."
                time.sleep(3 * 60)
                count = 0
            print "Reconnecting to remote server..."
            connect_ftp()
            os.chdir(l_dir)
            ftp.cwd(r_dir)
            print "Retrying upload..."
    # Remove the ".ihs" extension after successful upload
    ftp.rename(l_file + ".ihs", l_file)


#####################################
#
#  In a given model's base directory, missing_dirs finds any missing 
#  subdirectories (or random files).
#  Returns a list with the full local path of missing item,
#  remote parent directory of missing item, and missing item name.
#
#####################################
def missing_dirs():
    global logg
    issue_list = []
    for LocalDir in DevDirs:
        for RemoteDir in FTPDirs:
            if LocalDir[0] == RemoteDir[0]:
                print "Checking %s folder" % LocalDir[0]
                g_list = ftp_listing(RemoteDir[1])
                os.chdir(LocalDir[1])
                c_list = os.listdir(".")
                for c in c_list: # Check each folder (or file)...
                    if "CVS" in c and os.path.isdir(c):
                        continue
                    if c not in g_list: # against remote listing
                        print c, "will be uploaded"
                        logg += str(c) + " will be uploaded\n"
                        # Local directory, remote directory, missing folder
                        issue_list.append((os.getcwd() + "\\" + c, RemoteDir[1], c))
    return issue_list


#####################################
#
#  Takes a list of full local paths, parent remote paths and missing
#  folder (or file) then creates missing directories and uploads
#  missing files.
#
#####################################
def new_dirs(issue_list):
    for issue in issue_list:
        g_size = 0
        if os.path.isfile(issue[0]): # If file
            # It is a file so change to the local parent 
            # directory and remotely, then copy it over.
            os.chdir(issue[0][:-len(issue[2])])
            ftp.cwd(issue[1])
            ftp_up(issue[2], issue[0][:-len(issue[2])], issue[1])     
        else:  # Else it is a directory
            os.chdir(issue[0]) # Into missing directory
            ftp.cwd(issue[1]) # Into parent directory of missing
            ftp.mkd(issue[2]) # Make missing directory
            print "Made %s/%s" % (issue[1], issue[2])
            # Change remote directory, copy all files
            ftp.cwd(issue[1] + "/" + issue[2]) # Into missing directory
            files = os.listdir(".")
            for f in files:
                if "Thumbs.db" in f:   # Kind of useless file
                    continue
                if "~$" == f[0:2] and "docx" in f:
                    continue
                # Check to see if each is a file or a directory
                if os.path.isdir(issue[0] + "\\" + f): # If directory
                    new_dirs((issue[0]+"\\"+f, issue[1]+"/"+issue[2], f))
                else:  # It is a file...
                    ftp_up(f, issue[0], issue[1] + "/" + issue[2])


#####################################
#
#  Checks every item in the given folders, uploading missing files
#  and recursively uploading missing directories.
#
#####################################
def brute_force_check(C, G):
    # Change directories and get directory listings
    g_list = ftp_listing(G)
    days_back_to_check = 5 # Ignore folders not modified this recently.
    os.chdir(C)
    c_list = os.listdir(".")
    # For each item, it is either missing or not, and file or a folder
    for c in c_list:
        if ( (os.path.isdir(c) and "CVS" in c) or ("Thumbs.db" in c) or
             (".py" in c) or (".xlsx" in c) or ("~$" == c[0:2] and "docx" in c)):
            continue
                    
        os.chdir(C)
        ## TIME CHECK ## Comment out to check EVERYTHING ##
        days_since = (float(time.time())-float(os.path.getmtime(c)))/(60*60*24)
        if days_since > days_back_to_check:
            continue
        ## TIME CHECK ## Comment out to check EVERYTHING ##
        if c not in g_list: # Is it missing?
            if os.path.isdir(c): # Is it a directory?
                new_dirs([(C+"\\"+c, G, c)])
            else: # Or a file...
                ftp_up(c, C, G)
        else:
            if os.path.isdir(c): # Existing directory
                brute_force_check(C+"\\"+c, G+"/"+c) # Go into it
                ftp.cwd(G)
            else: # Existing file
                ftp.sendcmd("TYPE i")
                if ftp.size(c) != os.path.getsize(c):
                    print "Size mismatch:\n%s/%s" % (G, c)
                    # Different file size?  Copy new one over.
                        # second thought, let's not make a backup
                    #try: ftp.delete(c+".szmm") # Get rid of any backup.
                    #except: pass
                    #ftp.rename(c, c+".szmm") # Create backup.
                    ftp_up(c, C, G)

#####################################
#
#  The program checks for missing SIL directories in the base
#  directory for each SIL database, uploads any missing files.
#  It then checks every file that has been modified in the past
#  month to make sure it exists on the Garmin side and is the
#  appropriate size.  A wrong size indicates changed files on
#  Cessna's side or a failed file transfer.
#
#  The program can be easily changed to check EVERY folder,
#  subfolder and file instead of recently changes ones by
#  commenting out the "TIME CHECK" section in brute_force_check.
#
#####################################
def main(argv):
    global logg
    local_dir = os.getcwd()
    logg = ""
    sync_period = 0.5 # every x hours
    sync_p_late = 3
    
    timer = "ftp_sync_timer.txt"
    # When script was running constantly, this prevents it from running immediately after a crash
##    if os.path.isfile(timer):
##        hours_since = (float(time.time())-float(os.path.getmtime(timer)))/(60*60)
##        if hours_since < .25: # Wait at least 15 minutes from last try
##            time.sleep(60*60*(sync_period - hours_since))
##    try: 
##        f = open(timer, 'a')
##    except IOError: 
##        pass
##    f.write(logg)
##    f.close()
    
    while True:
        issues = []
        # Start FTP connection
        connect_ftp()

        # Find missing folders
        print "Making first pass for missing folders..."
        issues = missing_dirs()
        if issues:
            # Create missing folders, copy contained files
            try:
                new_dirs(issues)
            except:
                pass
        else:
            print "No missing folders found."

        # Check ALL folders and compare file contents...
        print "\nChecking all files in recently modified folders..."
        for LocalDir in DevDirs:
            for RemoteDir in FTPDirs:
                if LocalDir[0] == RemoteDir[0]:
                    print "Looking in %s folder." % LocalDir[0]
                    try:
                        brute_force_check(LocalDir[1], RemoteDir[1])
                    except:
                        print "Network error..."
        u_time = time.localtime(time.time())
        print "Finished at %d %d/%d %02d%02d\n" % \
        (u_time[0], u_time[1], u_time[2], u_time[3], u_time[4])
        logg += "Finished at %d %d/%d %02d%02d\n" % \
        (u_time[0], u_time[1], u_time[2], u_time[3], u_time[4])
        try:
            ftp.quit()
        except:
            pass # Oh well, if it can't quit it already quit.

        os.chdir(local_dir)

        # 'Writing to config file...\n'
        try: 
            f = open(timer, 'a')
        except IOError: 
            pass
        f.write(logg)
        f.close()

        logg = ""
        break # Adapted from version that checked periodically to just running once
    
    ans = raw_input("FTP Sync Complete")
    

if __name__ == '__main__':
    main(sys.argv)
