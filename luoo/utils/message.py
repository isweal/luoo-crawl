from colorama import Fore


def colorful_text(text, color=Fore.RESET):
    """make target text colorful

    :param text: target text
    :param color
    :return: colored text
    """
    return color + text + Fore.RESET


def error_message(message='Ops, there are some error...'):
    """print the error message in red color

    :param message: error message
    :return: None
    """
    print(colorful_text(message, Fore.RED))


def error(message='Ops, there are some error...'):
    """print the error message in red color

    :param message: error message
    :return: None
    """
    print(colorful_text(message, Fore.RED))


def notice(message, color=Fore.RESET):
    print(colorful_text(message, color))
