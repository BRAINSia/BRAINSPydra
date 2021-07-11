stdout = """==============================================================
qname        all.q
hostname     argon-itf-bx47-01.hpc
group        its-rs-user
owner        cjohnson30
project      NONE
department   defaultdepartment
jobname      Registration.15c13273826b436fb2f9baaeae1e245a
jobnumber    5734057
taskid       5
account      sge
priority     10
qsub_time    Thu Jun 17 20:25:57 2021
start_time   Thu Jun 17 20:26:10 2021
end_time     Thu Jun 17 20:30:35 2021
granted_pe   smp
slots        16
failed       0
exit_status  137                  (Killed)
ru_wallclock 265s
ru_utime     1.962s
ru_stime     0.683s
ru_maxrss    48.141KB
ru_ixrss     0.000B
ru_ismrss    0.000B
ru_idrss     0.000B
ru_isrss     0.000B
ru_minflt    288154
ru_majflt    28
ru_nswap     0
ru_inblock   43376
ru_oublock   0
ru_msgsnd    0
ru_msgrcv    0
ru_nsignals  0
ru_nvcsw     2351
ru_nivcsw    157
cpu          3124.570s
mem          4.877TBs
io           277.032MB
iow          0.000s
maxvmem      1.776GB
arid         undefined
ar_sub_time  undefined
category     -U HJ,INFORMATICS,COE,COE-GPU -u cjohnson30 -q all.q -pe smp 16
==============================================================
qname        all.q
hostname     argon-itf-bx48-24.hpc
group        its-rs-user
owner        cjohnson30
project      NONE
department   defaultdepartment
jobname      Registration.15c13273826b436fb2f9baaeae1e245a
jobnumber    5734057
taskid       3
account      sge
priority     10
qsub_time    Thu Jun 17 20:25:57 2021
start_time   Thu Jun 17 20:26:10 2021
end_time     Thu Jun 17 20:30:35 2021
granted_pe   smp
slots        16
failed       0
exit_status  137                  (Killed)
ru_wallclock 265s
ru_utime     2.198s
ru_stime     0.727s
ru_maxrss    48.141KB
ru_ixrss     0.000B
ru_ismrss    0.000B
ru_idrss     0.000B
ru_isrss     0.000B
ru_minflt    288136
ru_majflt    28
ru_nswap     0
ru_inblock   43376
ru_oublock   0
ru_msgsnd    0
ru_msgrcv    0
ru_nsignals  0
ru_nvcsw     2336
ru_nivcsw    158
cpu          3118.490s
mem          4.996TBs
io           292.234MB
iow          0.000s
maxvmem      1.837GB
arid         undefined
ar_sub_time  undefined
category     -U HJ,INFORMATICS,COE,COE-GPU -u cjohnson30 -q all.q -pe smp 16"""

def _verify_exit_code(stdout):
    # Read the qacct stdout into dictionary stdout_dict
    stdout_dict = {}
    for line in stdout.splitlines():
        line_split = line.split(None, 1)
        if len(line_split) > 1:
            if line_split[0] == "failed" and line_split[1] != "0":
                return "ERRORED"
    #     if len(key_value) > 1:
    #         stdout_dict[key_value[0]] = key_value[1]
    #     else:
    #         stdout_dict[key_value[0]] = None
    # if not stdout:
    #     return "ERRORED"

    # if [int(s) for s in stdout_dict["failed"].split() if s.isdigit()][0] == 0:
    #     return True
    # else:
    #     return "ERRORED"  # SGE job failed
    return True

print(_verify_exit_code(stdout))