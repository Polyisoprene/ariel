import click
from os import path, getcwd, mkdir
import dotenv
import nonebot


env = {
    'DRIVER':'~fastapi',
    'SUPERUSERS': [],
    'HOST':"127.0.0.1",
    'PORT':12315,
    'COMMAND_START':["/"]
}


@click.group()
def main():
    pass


@click.command()
def run():
    create_config()
    create_plugins_dir()
    from .bot import app
    nonebot.run(app=app)


main.add_command(run)


def create_config():
    env_file_path = path.join(getcwd(), ".env.prod")
    if not path.exists(env_file_path):
        for key, value in env.items():
            dotenv.set_key(
                env_file_path,
                key,
                str(value).replace(' ', ''),
                quote_mode="never"
            )


def create_plugins_dir():
    plugins_dir_path = path.join(getcwd(), "plugins")
    if not path.exists(plugins_dir_path):
        mkdir(plugins_dir_path)


