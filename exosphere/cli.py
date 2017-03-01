import clize
from . import stacks


def update(stack_type, *args):
    stacks.get(stack_type).update(*args)


def main():
    clize.run([stacks.staticsite])


if __name__ == '__main__':
    main()
