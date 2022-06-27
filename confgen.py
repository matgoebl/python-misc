#!/usr/bin/env python3
import io
import os
import sys
import logging
import yaml
import click


@click.group()
@click.option('-i', '--input', help='Input config.', type=click.File('rb'))
@click.option('-v', '--verbose', count=True)
@click.pass_context
def confgen(ctx, input, verbose):
    """Config generator."""
    logging.basicConfig(level=logging.WARNING-10*verbose,handlers=[logging.StreamHandler()],format="[%(levelname)s] %(message)s")
    ctx.obj = {}
    ctx.obj['input_conf'] = YamlConf(input)


@confgen.command()
@click.option('-o', '--output', help='Output config.', type=click.File('rb+'))
@click.pass_obj
def baselist(obj,output):
    output_conf = YamlConf(output)

    output_conf.data = obj['input_conf'].data
    output_conf.save()

#    click.echo(f"Debug is {'on' if ctx.obj['DEBUG'] else 'off'}")









class YamlConf:
    def __init__(self, file):
        self.data = {}
        self.modified = False
        if isinstance(file, io.BufferedReader) or isinstance(file, io.BufferedRandom):
            self.load(file)
        else:
            with open(file) as file:
                self.load(file)

    def load(self, file):
        self.filename = file.name
        logging.info(f"Reading {self.filename}")
        self.data = yaml.load(file, Loader=yaml.BaseLoader)
        self.label = os.path.basename( os.path.splitext(self.filename)[0] )
        logging.debug(f"Read Data {self.label}:\n{self}")

    def save(self, filename = None):
        if not filename:
            filename = self.filename
        logging.info(f"Writing {filename}")
        with open(filename, 'w') as file:
            yaml.dump(self.data, file)
        logging.debug(f"Wrote Data {self.label}:\n{self}")

    def __str__(self):
        return yaml.dump(self.data)



if __name__ == '__main__':
    confgen(auto_envvar_prefix='CONFGEN')
