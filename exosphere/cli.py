import clize
from . import stacks


def update(stack_type):
    stacks.get(stack_type).update()


def main():
    clize.run(cumulus)


if __name__ == '__main__':
    main()
