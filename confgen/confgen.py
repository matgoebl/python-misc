#!/usr/bin/env python3
import io
import os
import sys
import logging
import re
import copy
import ruamel.yaml
import pyhocon
import click
import collections


@click.group()
@click.option('-i', '--input', help='Input config.', type=click.File('rb'))
@click.option('-v', '--verbose', count=True)
@click.pass_context
def confgen(ctx, input, verbose):
    """Config generator."""
    logging.basicConfig(level=logging.WARNING-10*verbose,handlers=[logging.StreamHandler()],format="[%(levelname)s] %(message)s")
    ctx.obj = {}
    ctx.obj['input_conf'] = {}
    if input:
        ctx.obj['input_conf'] = YamlConf(input, strip_comments = True)


@confgen.command()
@click.option('-i', '--input',  help='Input config.',  type=click.File('r+'), required=True)
@click.option('-o', '--output', help='Output config.', type=click.File('w'))
@click.option('-m', '--mode', default='merge', type=click.Choice(['merge', 'replace', 'add', 'delete', 'filter'], case_sensitive=False))
@click.pass_obj
def yamllist(obj,input,output,mode):
    output_conf = YamlConf(input, reorder_comments = True)

    updates = obj['input_conf'].data

    output_conf.apply_changeset( updates['hosts'], updates['global'], mode)

    output_conf.save(output or input)


@confgen.command()
@click.option('-i', '--input',  help='Input config.',  type=click.File('r+'), required=True)
@click.option('-o', '--output', help='Output config.', type=click.File('w'))
@click.option('-m', '--mode', default='replace', type=click.Choice(['replace', 'delete'], case_sensitive=False))
@click.pass_obj
def hoconlist(obj,input,output,mode):
    output_conf = HoconConf(input)

    updates = obj['input_conf'].data

#    output_conf.apply_changeset( updates['hosts'], updates['global'], mode)

    for key in updates['hosts']:
        if mode == 'replace' or mode == 'delete':
            output_conf.remove(key)
        if mode != 'delete':
            changes = {}
            changes.update(copy.deepcopy(updates['global']))
            changes.update(copy.deepcopy(updates['hosts'][key]))
            logging.debug(f"Updating {key} with {changes}")
            output_conf.merge(key, changes)

    output_conf.save(output or input)



class KeyedConf:
    def __init__(self):
        self.data = {}
        self.modified = False

    def __str__(self):
        buf = io.StringIO()
        yaml = ruamel.yaml.YAML()
        yaml.dump(self.data, buf)
        return buf.getvalue()

    def add(self, key, value):
        if key in self.data:
            #raise Exception(f"Adding {key} failed, because it already exists.")
            logging.warning(f"Adding {key} failed, because it already exists.")
        self.data[key] = value

    def remove(self, key):
        if key in self.data:
            del self.data[key]

    def merge(self, key, value):
        if key in self.data:
            self.data[key].update(value)
        else:
            self.add(key, value)

    def keys(self):
        return list(self.data.keys())

    def apply_changeset(self, keyed_changes = {}, global_changes = {}, mode = 'merge'):
        keyed_changes = keyed_changes or {}
        
        logging.info(f"Apply changeset in mode {mode}")
        if mode == 'filter':
            for key in self.keys():
                if not key in keyed_changes:
                    self.remove(key)
        else:
            for key in keyed_changes:
                if mode == 'replace' or mode == 'delete':
                    self.remove(key)
                if mode == 'delete':
                    continue
                changes = {}
                changes.update(copy.deepcopy(global_changes or {}))
                changes.update(copy.deepcopy(keyed_changes[key]))
                logging.debug(f"Updating {key} with {changes}")
                if mode == 'merge':
                    self.merge(key, changes)
                if mode == 'add' or mode == 'replace':
                    self.add(key, changes)




class YamlConf(KeyedConf):
    def __init__(self, file, reorder_comments = False, strip_comments = False):
        super().__init__()
        self.reorder_comments = reorder_comments
        self.strip_comments = strip_comments
        self.yaml = ruamel.yaml.YAML()
        self.yaml.indent(mapping=2, sequence=4, offset=2)
        if isinstance(file, io.BufferedReader) or isinstance(file, io.BufferedRandom) or isinstance(file, io.TextIOWrapper):
            self.load(file)
        else:
            with open(file, 'r') as file:
                self.load(file)

    def load(self, file):
        self.filename = file.name
        logging.info(f"XReading {self.filename}")

        lines = file.read()
        if self.reorder_comments:
            lines = comments_postpone(lines)

        self.data = self.yaml.load(lines)
        self.label = os.path.basename( os.path.splitext(self.filename)[0] )
        logging.debug(f"Read Data {self.label}:\n{self}")

    def save(self, file = None):
        if not isinstance(file, str):
            filename = file.name
        else:
            filename = file
        if not filename:
            filename = self.filename
        logging.info(f"Writing {filename}")
        with open(filename, 'w') as file:
            lines = str(self)
            if self.reorder_comments:
                lines = comments_prepone(lines)
            elif self.strip_comments:
                lines = comments_strip(lines)
            file.write(lines)

        logging.debug(f"Wrote Data {self.label}:\n{self}")



def comments_strip(text):
    lines = ''
    for line in text.split('\n'):
        line = line + '\n'
        if not re.search(r'^\s*(#.*)?[\r\n]*$', line):
            lines = lines + line
    lines = lines.rstrip('\n')
    return lines

def comments_postpone(text):
    comment = ''
    lines = ''
    for line in text.split('\n'):
        logging.debug(f"READ {line}")
        line = line + '\n'
        if re.search(r'^\s*(#.*)?[\r\n]*$', line):
            comment = comment + line
            logging.debug(" COMMENT")
        else:
            lines = lines + line + comment
            comment = ''
    comment = comment.rstrip('\n')
    lines = lines + comment
    return lines

def comments_prepone(text):
    comment = ''
    noncomment = ''
    lines = ''
    for line in text.split('\n'):
        logging.debug(f"READ {line}")
        line = line + '\n'
        if re.search(r'^\s*(#.*)?[\r\n]*$', line):
            comment = comment + line
            logging.debug(" COMMENT")
        else:
            lines = lines + comment + noncomment
            comment = ''
            noncomment = line
    comment = comment.rstrip('\n')
    lines = lines + comment + noncomment
    return lines



class HoconConf(KeyedConf):
    def __init__(self, file):
        self.data = {}
        self.modified = False
        if isinstance(file, io.BufferedReader) or isinstance(file, io.BufferedRandom):
            self.load(file.name)
        else:
            self.load(file)

    def load(self, filename):
        self.filename = filename
        logging.info(f"Reading {self.filename}")
        self.data = pyhocon.ConfigFactory.parse_file(self.filename)
        self.label = os.path.basename( os.path.splitext(self.filename)[0] )
        logging.debug(f"Read Data {self.label}:\n{self}")

    def save(self, file = None):
        if not isinstance(file, str):
            filename = file.name
        else:
            filename = file
        filename = filename or self.filename
        logging.info(f"Writing {filename}")
        with open(filename, 'w') as file:
            file.write(pyhocon.HOCONConverter.to_hocon(self.data))

    def __str__(self):
        data = to_dict(self.data.as_plain_ordered_dict())
        buf = io.StringIO()
        yaml = ruamel.yaml.YAML()
        yaml.dump(data, buf)
        return buf.getvalue()

    def add(self, key, value):
        if self.data.get(key, default=None):
            raise Exception(f"Adding {key} failed, because it already exists.")
        self.merge(key, value)

    def remove(self, key):
        self.data.pop(key, default=None)

    def merge(self, key, value):
        ct = to_conftree(key, value)
        self.data = pyhocon.ConfigTree.merge_configs(self.data, ct)


def to_conftree(basekey, val, ct=None):
    if not ct:
        ct = pyhocon.ConfigTree()
    for k, v in val.items():
        if isinstance(v, dict) or isinstance(v, collections.OrderedDict):
            to_conftree(basekey + "." + k, v, ct)
        else:
            ct.put(basekey + "." + k, v)
    return ct


def to_dict(val):
    for k, v in val.items():
        if isinstance(v, dict):
            val[k] = to_dict(v)
    return dict(val)


if __name__ == '__main__':
    confgen(auto_envvar_prefix='CONFGEN')
