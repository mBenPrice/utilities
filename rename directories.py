import os, win32api, re


#####################################
#
#  A quick utility script that I used to batch rename many directories
#
#####################################

ds2rename = []

for folder in os.listdir(os.getcwd()):
    if os.path.isdir(folder):
        print folder
        temp = re.sub("2016","", folder)
        temp = "prepend_text" + temp
        ds2rename.append((folder, temp))

for d in ds2rename:
    print d[0],'\t---->\t',d[1]

ans = "nope"
while not (ans == "no" or ans == "yes"):
    ans = raw_input("Continue with rename? (yes, no)").lower()

if ans == "yes":
    for d in ds2rename:
        os.rename(d[0], d[1])
    ans = raw_input("Folders renamed.")
