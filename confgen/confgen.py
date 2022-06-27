#!/usr/bin/env python3
import io
import os
import sys
import logging
import copy
import ruamel.yaml
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

    updates = obj['input_conf'].data

    for key in updates['hosts']:
        changes = copy.deepcopy(updates['global'])
        changes.update(copy.deepcopy(updates['hosts'][key]))
        logging.debug(f"Updating {key} with {changes}")
        output_conf.merge(key, changes)

    output_conf.save()



class YamlConf:
    def __init__(self, file):
        self.data = {}
        self.modified = False
        self.yaml = ruamel.yaml.YAML(typ='safe')
        self.yaml.top_level_colon_align = True
        self.yaml.indent = 2
        self.yaml.mapping = 2
        if isinstance(file, io.BufferedReader) or isinstance(file, io.BufferedRandom):
            self.load(file)
        else:
            with open(file) as file:
                self.load(file)

    def load(self, file):
        self.filename = file.name
        logging.info(f"Reading {self.filename}")
        self.data = self.yaml.load(file)
        self.label = os.path.basename( os.path.splitext(self.filename)[0] )
        logging.debug(f"Read Data {self.label}:\n{self}")

    def save(self, filename = None):
        if not filename:
            filename = self.filename
        logging.info(f"Writing {filename}")
        with open(filename, 'w') as file:
            self.yaml.dump(self.data, file)
        logging.debug(f"Wrote Data {self.label}:\n{self}")

    def __str__(self):
        buf = io.StringIO()
        self.yaml.dump(self.data, buf, )
        return buf.getvalue()

    def add(self, key, value):
        self.data[key] = value

    def remove(self, key):
        del self.data[key]

    def merge(self, key, value):
        if key in self.data:
            self.data[key].update(value)
        else:
            self.add(key, value)



if __name__ == '__main__':
    confgen(auto_envvar_prefix='CONFGEN')
