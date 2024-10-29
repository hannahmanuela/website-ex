import os
import ctypes
import functools
from resource import *
import time

from flask import Flask
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


# define decorator

def add_deadline(deadline, methods = []):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            if len(methods) > 0 and request.method not in methods:
                result = func(*args, **kwargs)
                print("method ", request.method, " not in the set of allowed ones, skipping")
                return result

            num_cpus = os.cpu_count()
            affinity_mask = list(range(2, num_cpus))
            os.sched_setaffinity(0, affinity_mask)

            affinity = os.sched_getaffinity(0)

            ns_per_ms = 1000000
            attr = sched_attr()
            attr = sched_getattr(0, attr)

            attr.sched_runtime = deadline * ns_per_ms
            sched_setattr(0, attr)

            start_time = time.time() * 1000
            
            # Call the original function
            result = func(*args, **kwargs)

            attr.sched_runtime = 4 * ns_per_ms
            sched_setattr(0, attr)

            end_time = time.time() * 1000
            time_passed = end_time - start_time

            # also print out latency results
            usage_stats = getrusage(RUSAGE_THREAD)

            # stats are given in seconds, convert to ms
            runtime = usage_stats.ru_utime * 1000 + usage_stats.ru_stime * 1000
            f = open("latency.txt", "a")
            f.write(str(end_time) + " - latency: time passed: (inside: " + str(time_passed) + ", outside: " + str(time_passed) + "), deadline: " + str(deadline) + ", rusage: " + str(runtime) + "\n")
            f.close()

            return result
        return wrapper
    return decorator



def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="dev",
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # register the database commands
    from . import db

    db.init_app(app)

    # apply the blueprints to the app
    from . import blog
    from . import auth

    app.register_blueprint(blog.bp)
    app.register_blueprint(auth.bp)

    # make url_for('index') == url_for('blog.index')
    # in another app, you might define a separate main index here with
    # app.route, while giving the blog blueprint a url_prefix, but for
    # the tutorial the blog will be the main index
    app.add_url_rule("/", endpoint="index")

    open("latency.txt", 'w').close()

    affinity_mask = {1}
    os.sched_setaffinity(0, affinity_mask)

    return app
