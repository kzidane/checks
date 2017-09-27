import os
import re

from check50 import *

class Challenge(Checks):

    @check()
    def exists(self):
        """dictionary.c and dictionary.h exist"""
        self.require("dictionary.c", "dictionary.h")
        self.add("speller.c", "timer.c", "dictionaries", "texts", "sols")

    @check("exists")
    def compiles(self):
        """dictionary.c compiles"""
        self.spawn("clang -ggdb3 -O0 -Qunused-arguments -std=c11 -Wall -Werror -c -o speller.o speller.c").exit(0)
        self.spawn("clang -ggdb3 -O0 -Qunused-arguments -std=c11 -Wall -Werror -c -o dictionary.o dictionary.c").exit(0)
        self.spawn("clang -ggdb3 -O0 -Qunused-arguments -std=c11 -Wall -Werror -o speller speller.o dictionary.o").exit(0)
        self.spawn("clang -ggdb3 -O0 -Qunused-arguments -std=c11 -Wall -Werror -c -o timer.o timer.c").exit(0)
        self.spawn("clang -ggdb3 -O0 -Qunused-arguments -std=c11 -Wall -Werror -o timer timer.o dictionary.o").exit(0)

    @check("compiles")
    def qualifies(self):
        """qualifies for Big Board"""
        try:

            # Run on kjv.txt
            self.spawn("./speller dictionaries/large texts/kjv.txt > actual.out").exit(0, timeout=20)
            actual = open("actual.out").read().splitlines()
            expected = open("sols/kjv.txt").read().splitlines()

            # Compare output line for line.
            if len(actual) != len(expected):
                raise Error("{} lines expected, not {}".format(len(expected), len(actual)))
            for actual_line, expected_line in zip(actual, expected):
                if actual_line != expected_line:
                    raise Error("expected {}, not {}".format(expected_line, actual_line))

        # Clear log to avoid clutter.
        except Error as e:
            raise e

    @check("qualifies")
    def benchmark(self):
        """passes benchmarking"""

        # Timing data.
        self.data["time"] = {
            "load": 0.0,
            "check": 0.0,
            "size": 0.0,
            "unload": 0.0
        }
        for text in os.listdir("texts"):
            out = self.spawn("./timer dictionaries/large texts/{}".format(text)).stdout(timeout=20)
            load, check, size, unload = map(float, out.split())
            self.data["time"]["load"] += load
            self.data["time"]["check"] += check
            self.data["time"]["size"] += size
            self.data["time"]["unload"] += unload
        self.data["time"]["total"] = self.data["time"]["load"] + self.data["time"]["check"] + \
                                     self.data["time"]["size"] + self.data["time"]["unload"]


        # Memory data.
        self.spawn("valgrind --tool=massif --heap=yes --stacks=yes --massif-out-file=massif.out ./speller dictionaries/large texts/holmes.txt").stdout(timeout=20)
        f = open("massif.out")

        heap = 0
        stack = 0
        re_heap = re.compile("mem_heap_B=(\d+)")
        re_stack = re.compile("mem_stacks_B=(\d+)")
        for line in f:
            heap_match = re_heap.match(line)
            stack_match = re_stack.match(line)
            if heap_match:
                heap = max(heap, int(heap_match.groups()[0]))
            elif stack_match:
                stack = max(stack, int(stack_match.groups()[0]))

        self.data["memory"] = {
            "stack": stack,
            "heap": heap
        }
