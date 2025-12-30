#!/bin/python3

import sys
import subprocess
import sqlite3
import re

class App:
    def __init__(self, name_real, name_pretty, description = None):
        self.name_real = name_real
        self.name_pretty = name_pretty
        self.description = description

min_argc = 2

if len(sys.argv) < min_argc:
    print("Usage: clean.py <database>");    
    exit(1)

database_file = sys.argv[1]

conn = sqlite3.connect(database_file)
cur = conn.cursor();

adb_proc = subprocess.Popen(["/usr/bin/adb", "shell", "pm", "list", "packages"], stdout=subprocess.PIPE)
out, err = adb_proc.communicate()
out_str = out.decode("utf-8")[0:max(len(out) - 1, 0)]

out_lines = out_str.split('\n')
for l in out_lines:
    if re.match(r"^package:[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)*$", l) == None:
        raise SyntaxError("Output from adb is invalid:\n'" + l + "'");

found_pups = list();

longest_pup_real_name = 0

for line in out_lines:
    package_name = line.split(":")[1]
    cur.execute("SELECT name_real, name_pretty, description FROM pups WHERE name_real=?;", [package_name])
    q_res = cur.fetchone()

    if q_res == None:
        continue

    app = App(q_res[0], q_res[1], q_res[2])
    found_pups.append(app)
    if len(app.name_real) > longest_pup_real_name:
        longest_pup_real_name = len(app.name_real)

conn.close()

if len(found_pups) == 0:
    print("No PUPs found!");
    exit(0);
else:
    print(str(len(found_pups)) + " PUP(s) found:");
    print("\n", end="");
    for pup in found_pups:
        print("  " + pup.name_real + (" " * (longest_pup_real_name - len(pup.name_real))) + "    (" + pup.name_pretty + ")");
        if pup.description != None:
            print("      " + pup.description)
        print("\n", end="")
        
    print("\n", end="");
    print("Would you like to delete these apps? [Y/n]");

    delete_confirm = input();
    if delete_confirm == "Y":
        for pup in found_pups:
            uninstall_proc = subprocess.Popen(["adb", "uninstall", pup.name_real], stdout=subprocess.PIPE);
            out, err = uninstall_proc.communicate();

            print("  [*] Attempting to delete " + app.name_real + "  (" + app.name_pretty + ")...");
            if(out == b"Success\n"):
                print("  [x] Deleted " + app.name_real + ".  (" + app.name_pretty + ")");
            else:
                print("Failed to delete " + app.name_real + ".  (" + app.name_pretty + ")");
                print("Message: " + out.decode("utf-8"))
