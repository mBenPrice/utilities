import wmi, os, sys, time, re, subprocess
from win32com import client

to = ["me@gmail.com"]
c = wmi.WMI()
procs = []
init = True

#####################################
#
#  Sends an email to globally defined email address
#
#####################################
def SendMail(subj, msg):
    rcpts = ''
    olMailItem = 0x0
    obj = client.Dispatch("Outlook.Application")
    newMail = obj.CreateItem(olMailItem)
    newMail.Subject = subj
    newMail.Body = msg
    
    for ppl in to:
        rcpts += ppl + ";"
    newMail.To = rcpts
    print "\nSending:  " + newMail.Subject + "\n" + msg
    newMail.Send()

#####################################
#
#  Old function that initiated an FTP sync if a certain email was received
#
#####################################
def ftp_launch_check():
    try:
        obj = client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    except:
        return
    try:
        inbox = obj.GetDefaultFolder(6)
        messages = inbox.Items
        message = messages.GetLast()
        subj = message.Subject.lower()
        sender = message.SenderEmailAddress
    except:
        return
    if "run ftp sync" in subj:
        subprocess.Popen(['cmd.exe',"/c"+os.getcwd()+ \
                                      "\\quick_ftp_sync.py"])
        message.Delete()


#####################################
#
#  Processes .txt file and populates global variable procs
#
#####################################
def config():
    global procs
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    procs = []
    try: 
        f = open('controller_config.txt', 'r+')
    except IOError: 
        print 'controller_config.txt file no collocated with script...\n'
        return 1

    # Populating processes list from config.txt file
    if init:
        print "Watching for:"
    for line in f:          
        if line[0] == '#':
            continue
        line = line.rstrip()
        if ' ' in line:
            spidx = line.find(' ') # Identify passed arguments
            procs.append((line[:spidx] + line[spidx:], -1))
            print line[:spidx] + line[spidx:]
        else:
            procs.append((line, -1))
            print line
    f.close()


#####################################
#
#  Returns list of Python scripts running on Windows
#
#####################################
def GetProcs():
    retval = []
    for process in c.Win32_Process():
        if "python.exe" in str(process.Name):
            temp = str(process.CommandLine)
            while temp.find('\\') > 0:
                temp = temp[temp.find('\\')+1:]
            end  = temp[3+temp.find('"'):-1]
            temp = temp[:temp.find('"')]
            if end:
                retval.append((temp + ' ' + end))
            else:
                retval.append(temp)
    return retval

#####################################
#
#  Launches and monitors progress of .py files specified in .txt file,
#  restarts failed processes if necessary, using a saturation counter in
#  case of repeated crashes
#
#####################################
def main(argv):
    global init
    daily_trigger = False
    count = 0
    inc = 1
    maxval = 15
    sat_count = 0
    config()
    

  
    while True:
        count += inc
        sys.stdout.write("\r" + "=" * count + " " * (maxval - count))
        sys.stdout.flush()
        
        if count == maxval:
            temp = 'Still running:\n'
            inc = -1
            p_list = GetProcs()
            for idx,p in enumerate(procs):
                temp += str(p) + '\n'

                if procs[idx][0] not in p_list and procs[idx][1] < 2:
                    subprocess.Popen(['cmd.exe',"/c"+os.getcwd()+ \
                                      "\\"+procs[idx][0]])
                    if not init:
                        SendMail("Python Down Notification", \
                                 str(procs[idx]) + " was down, restarted")
                                            # Saturation counter
                        procs[idx] = (procs[idx][0], procs[idx][1]+1) 
                                
                if sat_count == 50:         # Saturation counter
                    if procs[idx][1] >= 0:
                        procs[idx] = (procs[idx][0], procs[idx][1]-1)
                    sat_count = 0
                else:
                    sat_count += 1
            init = False
            
        if count == 0:
            inc = 1
        time.sleep(0.3)
        
        if (daily_trigger and time.localtime().tm_hour < 4 and
                    time.localtime().tm_mday % 4):
            SendMail("PD Still Running", temp)
            daily_trigger = False
        elif time.localtime().tm_hour > 5:
            daily_trigger = True
            

            


if __name__ == '__main__':
    main(sys.argv)
