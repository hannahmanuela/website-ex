import os
import ctypes
import functools
from resource import *
import time
from dataclasses import dataclass

from flask import Flask, jsonify
from flask import request


# setup to make syscalls

libc = ctypes.CDLL(None, use_errno=True)

class sched_attr(ctypes.Structure):
    _fields_ = [
        ('size', ctypes.c_uint32),
        ('sched_policy', ctypes.c_uint32),
        ('sched_flags', ctypes.c_uint64),
        ('sched_nice', ctypes.c_int32),
        ('sched_priority', ctypes.c_uint32),
        ('sched_runtime', ctypes.c_uint64),
        ('sched_deadline', ctypes.c_uint64),
        ('sched_period', ctypes.c_uint64),
    ]

def sched_getattr(pid, attr):
    attr.size = ctypes.sizeof(attr)
    ret = libc.syscall(315, pid, ctypes.byref(attr), attr.size, 0)
    if ret == -1:
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))
    return attr


def sched_setattr(pid, attr):
    attr.size = ctypes.sizeof(attr)
    ret = libc.syscall(314, pid, ctypes.byref(attr), 0)
    if ret == -1:
        errno = ctypes.get_errno()
        raise OSError(errno, os.strerror(errno))

# this is a structure that will be global, how do I do that? is create_app only run exactly once?

def curr_time_ms():
    return int(round(time.time() * 1000))

@dataclass
class Proc:
    tid: int
    deadline: int
    max_comp: int
    time_started: int

    def get_slack(self):
        og_slack = self.deadline - self.max_comp
        # print("returning slack of ", og_slack - self.wait_time(), "w/ og slack being ", og_slack)
        return og_slack - self.wait_time()
    
    def time_gotten(self):
        # time passed - time waiting
        return (curr_time_ms() - self.time_started) - self.wait_time()

    def get_expected_comp_left(self):  
        return self.max_comp - self.time_gotten()
    
    
    def wait_time(self):
        try:
            with open(f"/proc/{self.tid}/schedstat", "r") as f:
                line = f.readline()
                values = line.split()
                return int(values[1])/ 1000000
        except FileNotFoundError:
            return None


def do_admission_control(new_proc):

    global core_to_proc_mapping

    for core_num, curr_list in core_to_proc_mapping.items():
        pot_new_list = curr_list + [new_proc]
        pot_new_list = sorted(pot_new_list, key=lambda proc: proc.deadline)

        wait_time = 0
        fits = True
        for p in pot_new_list:
            if p.get_slack() - wait_time < 0:
                print("doesnt fit, slack is ", p.get_slack(), "but wait time is currently", p.get_expected_comp_left())
                fits = False
                break
            wait_time += p.get_expected_comp_left()
        
        if (fits):
            core_to_proc_mapping[core_num].append(new_proc)
            return True, core_num
    
    return False, -1


core_to_proc_mapping = {c: [] for c in range(os.cpu_count())}

ns_per_ms = 1000000

# define decorator

def add_deadline(max_comp, deadline, methods = []):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            if len(methods) > 0 and request.method not in methods:
                result = func(*args, **kwargs)
                return result

            global core_to_proc_mapping
            global ns_per_ms

            new_proc = Proc(libc.gettid(), deadline * ns_per_ms, max_comp * ns_per_ms, curr_time_ms())
            admitted, core_to_use = do_admission_control(new_proc)

            print("admitted? ", admitted)

            if not admitted:
                return jsonify({'error': 'admission control rejected'}), 120

            print("placed on core ", core_to_use)

            # set the cpu affinity based on what the admission control said
            affinity_mask = {core_to_use}
            os.sched_setaffinity(0, affinity_mask)

            affinity = os.sched_getaffinity(0)


            # set the kernel sched runtime to be deadline
            attr = sched_attr()
            attr = sched_getattr(0, attr)

            attr.sched_runtime = deadline * ns_per_ms
            sched_setattr(0, attr)

            start_time = time.time() * 1000
            
            # Call the original function
            result = func(*args, **kwargs)

            # "clear" ie reset kernel sched deadline
            attr.sched_runtime = 4 * ns_per_ms
            sched_setattr(0, attr)

            end_time = time.time() * 1000
            time_passed = end_time - start_time

            # print out latency results
            usage_stats = getrusage(RUSAGE_THREAD)

            # stats are given in seconds, convert to ms
            runtime = usage_stats.ru_utime * 1000 + usage_stats.ru_stime * 1000
            f = open("latency.txt", "a")
            f.write(str(end_time) + " - latency: time passed: (inside: " + str(time_passed) + ", outside: " + str(time_passed) + "), deadline: " + str(deadline) + ", rusage: " + str(runtime) + "\n")
            f.close()

            return result
        return wrapper
    return decorator



def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="dev",
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )

    # if test_config is None:
        # load the instance config, if it exists, when not testing
    app.config.from_pyfile("config.py", silent=True)
    # else:
        # load the test config if passed in
        # app.config.update(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # apply the blueprints to the app
    from . import model_app

    app.register_blueprint(model_app.bp)

    # make url_for('index') == url_for('blog.index')
    # in another app, you might define a separate main index here with
    # app.route, while giving the blog blueprint a url_prefix, but for
    # the tutorial the blog will be the main index
    app.add_url_rule("/", endpoint="index")

    open("latency.txt", 'w').close()

    affinity_mask = {1}
    os.sched_setaffinity(0, affinity_mask)

    return app
