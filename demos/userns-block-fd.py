#!/usr/bin/env python

import os, select, subprocess, json

pipe_info = os.pipe()
userns_block = os.pipe()

pid = os.fork()

if pid != 0:
    os.close(pipe_info[1])
    os.close(userns_block[0])

    select.select([pipe_info[0]], [], [])

    data = json.load(os.fdopen(pipe_info[0]))
    child_pid = str(data['child-pid'])

    subprocess.call(["newuidmap", child_pid, "0", str(os.getuid()), "1"])
    subprocess.call(["newgidmap", child_pid, "0", str(os.getgid()), "1"])

    os.write(userns_block[1], '1')
else:
    os.close(pipe_info[0])
    os.close(userns_block[1])

    args = ["bwrap",
            "bwrap",
            "--unshare-all",
            "--unshare-user",
            "--userns-block-fd", "%i" % userns_block[0],
            "--info-fd", "%i" % pipe_info[1],
            "--bind", "/", "/",
            "cat", "/proc/self/uid_map"]

    os.execl(*args)
