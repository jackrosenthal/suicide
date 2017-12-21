import threading
import sys
from stackcalc import StackCalculator
from queue import Queue

class DeathMessage:
    pass

class FileReadingQueue(threading.Thread):
    def __init__(self, f):
        self.f = f
        self.q = Queue()
        super().__init__()
        self.daemon = True

    def run(self):
        try:
            for line in self.f:
                for literal in line.split():
                    self.q.put(literal)
        except:
            pass

    def get(self, *args, **kwargs):
        return self.q.get(*args, **kwargs)

    def get_nowait(self, *args, **kwargs):
        return self.q.get_nowait(*args, **kwargs)

class FileWritingQueue(threading.Thread):
    def __init__(self, f):
        self.f = f
        self.q = Queue()
        super().__init__()

    def run(self):
        while True:
            item = self.q.get()
            if item is DeathMessage:
                break
            print(item, file=self.f)
        f.close()

    def put(self, *args, **kwargs):
        return self.q.put(*args, **kwargs)

    def put_nowait(self, *args, **kwargs):
        return self.q.put_nowait(*args, **kwargs)

features = {}
def feature(f):
    features[f.__name__] = f
    return f

class Executor(threading.Thread):
    def __init__(self, gen, talk_q=None, note_q=None):
        self.gen = gen
        self.talk_q = talk_q if talk_q else Queue()
        self.note_q = note_q if note_q else Queue()
        self.sc = StackCalculator()
        self.children = []
        self.dead = False
        super().__init__()

    def run(self):
        try:
            for ins in program:
                if self.dead:
                    break
                self.do(ins)

        except Exception as e:
            print("{} in {}:".format(e, self.name))
            print("    Instruction:", ' '.join(ins))
            print("    Memory stack:", self.sc._stack)
            print("    Children:", self.children)
            print()

    def do(self, ins):
        if ins and ins[0] in features.keys():
            features[ins[0]](self, *ins[1:])

    @feature
    def ask(self, *args):
        self.sc.push(self.talk_q.get())

    @feature
    def ponder(self, *args):
        item = self.sc.peek()
        if not item:
            self.do(args)

    @feature
    def memories(self, *args):
        for item in args:
            self.sc.push(item)

    @feature
    def breed(self, *args):
        child = Executor(gen=self.gen + 1)
        for tale in args[1:]:
            self.sc.push(tale)
            child.talk_q.put(self.sc.pop())
        child.start()
        self.children.append(child)

    @feature
    def suicide(self, *args):
        if args and args[0] == 'with':
            self.do(args[1:])
        else:
            try:
                self.note_q.put(self.sc.pop())
            except StackCalculator.StackEmptyError:
                pass
        self.note_q.put(DeathMessage)
        self.dead = True

    @feature
    def note(self, *args):
        if args[0] == 'story':
            while self.sc._stack:
                self.note_q.put(self.sc.pop())
            return
        for item in args:
            self.sc.push(item)
        self.note_q.put(self.sc.pop())

    @feature
    def murder(self, *args):
        if self.children:
            child = self.children.pop()
            while True:
                note = child.note_q.get()
                if note is DeathMessage:
                    break
                self.sc.push(note)
            child.join()
            if args and args[0] == 'family':
                self.murder('family')

    @feature
    def generation(self, *args):
        self.sc.push(self.gen)


if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        program = [line.split() for line in f]
    e = Executor(gen=0, talk_q=FileReadingQueue(sys.stdin), note_q=FileWritingQueue(sys.stdout))
    e.talk_q.start()
    e.note_q.start()
    e.start()
    e.join()
    e.note_q.join()
