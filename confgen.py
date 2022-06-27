#!/usr/bin/env python3
import os
import sys
import logging
import yaml
import click


@click.command()
@click.option('-i', '--input', help='Input config.')
@click.option('-v', '--verbose', count=True)
@click.pass_context
def confgen(ctx, input, verbose):
    """Config generator."""
    logging.basicConfig(level=logging.WARNING-10*verbose,handlers=[logging.StreamHandler()],format="[%(levelname)s] %(message)s")
    ctx.conf = Conf(input)


@confgen.command()
@confgen.option('-o', '--output', help='Output config.')
@click.pass_context
def baselist(ctx,output):
    a = 1
#    click.echo(f"Debug is {'on' if ctx.obj['DEBUG'] else 'off'}")









class Conf:
    def __init__(self, filename):
        self.filename = filename
        self.modified = False
        if filename:
            self.load_file(filename)
        self.data = {}

    def load_file(self, filename):
        logging.info(f"Reading {filename}")
        with open(filename) as f:
            self.data = yaml.load(f, Loader=yaml.BaseLoader)
            self.label = os.path.basename( os.path.splitext(filename)[0] )
            logging.debug(f"Data {self.label}:\n{self}")

    def __str__(self):
        return yaml.dump(self.data)



if __name__ == '__main__':
    confgen(auto_envvar_prefix='CONFGEN')
