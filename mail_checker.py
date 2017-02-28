import wmi, os, sys, time, re, subprocess
from win32com import client

c = wmi.WMI()

#####################################
#
#  Modifies a .html file that auto-refreshes itself in browser window
#  to notify of new email in case notification is missed
#
#####################################
def edit_page(count):
    output = ''
    with open('U:\start_page.htm', "r+") as sp:
        for line in sp:
            temp = line
            if "Start Page</title>" in line:
                if "Email" not in line and count:
                    temp = "<title>Email! Start Page</title>\r\n"
                else:
                    temp = "<title>Start Page</title>\r\n";
            elif "background-color" in line:
                temp = line[:line.index(':')+2]
                color = line[line.index(':')+2:]
                color = color[:color.index(';')]
                if color == "#cce6ff" and count:
                    color = "#f6e6f0";
                else:
                    color = "#cce6ff";
                temp += color + ";}\r\n"
            output += temp
        output.replace("</html></html>","</html>")
        sp.seek(0)
        sp.write(output)
        sp.truncate()
        

#####################################
#
#  Sees if any emails are in inbox, returns count
#
#####################################
def mail_check():
    count = 0

    try:
        obj = client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    except Exception, e:
        print e
        return count
    
    try:
        inbox = obj.GetDefaultFolder(6)
        messages = inbox.Items
        for m in messages:
            if m.Unread == True:
                count += 1

    except Exception, e:
        print e

    return count


#####################################
#
#  Modifies .html file if unread emails are in inbox
#
#####################################
def main(argv):
    count = 0
    inc = 1
    maxval = 25
    
    while True:
        count += inc
        
        if count == maxval:
            edit_page(mail_check())
            inc = -1
        elif count == 0:
            inc = 1
        time.sleep(0.2)


if __name__ == '__main__':
    main(sys.argv)
