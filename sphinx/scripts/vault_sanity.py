#! /usr/bin/env python
# NOTE: keep this a READ-ONLY script

import os
import json
import argparse
import re
import requests
from bs4 import BeautifulSoup
import subprocess
import time

def linking_sanity(subpart_dir, container_dir):
    print('Checking container-subpart linking')

    # build set of subpart names from dir
    dir_subparts = []
    for subpart in os.listdir(subpart_dir):
        if subpart.endswith('.json'):
            dir_subparts.append(subpart[:-5])

    dir_subparts_set = set(dir_subparts)

    # build set of subpart names from containers 
    container_subparts = []
    for container in os.listdir(container_dir):
        if container == 'img':
            continue
        with open(os.path.join(container_dir, container), 'r') as f: 
            try: 
                container_json = json.load(f)
            except ValueError as e:
                print('\nInvalid JSON in container %s' % container)
                raise e

            for subpart in container_json["subparts"]:
                container_subparts.append(str(subpart))

    container_subparts_set = set(container_subparts)

    if (len(dir_subparts) != len(container_subparts)):
        print('\nLength mismatch : dir - %s container - %s' % (dir_subparts, container_subparts))
    if (dir_subparts_set != container_subparts_set):
        print('\nElement mismatch : dir - %s container - %s' % (dir_subparts_set, container_subparts_set))

    print('Checking subpart indices')
    questions = 0
    for container in os.listdir(container_dir):
        if container == 'img':
            continue
        questions += 1
        with open(os.path.join(container_dir, container), 'r') as f: 
            container_json = json.load(f)
            for i, subpart in enumerate(container_json["subparts"]):
                # open subpart file to check its index
                with open(os.path.join(subpart_dir, str(subpart)+'.json'), 'r') as s: 
                    try: 
                        subpart_json = json.load(s)
                    except ValueError as e:
                        print('\nInvalid JSON in subpart %s' % subpart)
                        raise e

                    if i != subpart_json['subpart_index']:
                        print('\nindex mismatch for subpart: %s Expected: %s Found: %s' % (subpart, i, subpart_json['subpart_index']))

    print(str(questions) + ' questions verified')
    print('Done')


def html_sanity(subpart_dir, container_dir):
    for typestr, dirname in [('subpart', subpart_dir), ('container', container_dir)]:
        ctr = 0
        total = len(os.listdir(dirname))
        for fname in os.listdir(dirname):
            ctr += 1
            print('%s/%s' % (ctr, total))

            if fname == 'img':
                continue
            
            with open(os.path.join(dirname, fname), 'r') as f: 
                f_json = json.load(f)
                check_html(typestr, fname, f_json)

    print('Done')

VALIDATOR_JAR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'vnu.jar')
VALIDATOR_PORT = '9191'

def start_local_validation_server():
    print('Starting local validation server... this will take some time...')
    p = subprocess.Popen(['java', '-cp', VALIDATOR_JAR, 'nu.validator.servlet.Main', VALIDATOR_PORT], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    # allow server to start
    time.sleep(20)

def nu_html_validate(html_string, typestr, fname):
    headers = {'Content-Type': 'text/html; charset=utf-8'}
    validator = "http://localhost:9191"
    data = "<!DOCTYPE html><head><title>Vault HTML Sanity Test</title></head><body>%s</body>" % html_string

    while True:
        try:
            res = requests.post(validator, headers=headers, data=data)
            break
        except requests.exceptions.ConnectionError:
            start_local_validation_server()

    sp = BeautifulSoup(res.content, "html.parser")
    success = len(sp.find_all('p', class_='success')) > 0
    if not success:
        error_list = sp.find_all('ol')[0].find_all('li', class_='error')
        print('\n%s %s : Invalid HTML : %s' % (typestr, fname, html_string))
        print ('\nError messages:\n')
        for error in error_list:
            print('%s' % error.p.span.get_text())
        print('')
        
NON_HTML_KEYS = set(['condition'])

def check_html(typestr, fname, val):
    if isinstance(val, dict):
        for k,v in val.items(): 
            if k not in NON_HTML_KEYS:
                check_html(typestr, fname, v)
    elif isinstance(val, list):
        for e in val:
            check_html(typestr, fname, e)
    elif isinstance(val, str):
        nu_html_validate(val, typestr, fname)

def mathjax_sanity(subpart_dir, container_dir):
    print('Checking mathjax sanity')
    for typestr, dirname in [('subpart', subpart_dir), ('container', container_dir)]:
        for fname in os.listdir(dirname):
            if fname == 'img':
                continue
            
            with open(os.path.join(dirname, fname), 'r') as f: 
                f_json = json.load(f)
                check_mathjax(typestr, fname, f_json)

    print('Done')

def check_mathjax(typestr, fname, val):
    if isinstance(val, dict):
        for k,v in val.items(): 
            check_mathjax(typestr, fname, v)
    elif isinstance(val, list):
        for e in val:
            check_mathjax(typestr, fname, e)
    elif isinstance(val, str):
        mathjax_validate(val, typestr, fname)

def mathjax_validate(mathjax_string, typestr, fname):
    # check for matching delimiters
    delimiter1 = re.compile(r'\\\(')
    delimiter2 = re.compile(r'\\\)')
    delimiter3 = re.compile(r'\\\[')
    delimiter4 = re.compile(r'\\\]')

    count1 = len(re.findall(delimiter1, mathjax_string))
    count2 = len(re.findall(delimiter2, mathjax_string))
    count3 = len(re.findall(delimiter3, mathjax_string))
    count4 = len(re.findall(delimiter4, mathjax_string))

    if count1 != count2:
        print("\n%s %s : mathjax () delimiter mismatch in %s" % (typestr, fname, mathjax_string))
    if count3 != count4:
        print("\n%s %s : mathjax [] delimiter mismatch in %s" % (typestr, fname, mathjax_string))    

    # check for no html tags inside mathjax tags
    matcher1 = re.compile(r'\\\((.*?)\\\)')
    matcher2 = re.compile(r'\\\[(.*?)\\\]')
    matches1 = re.findall(matcher1, mathjax_string)
    matches2 = re.findall(matcher2, mathjax_string)

    for match_list in [matches1, matches2]:
        for match in match_list:
            if ('<' in match) or ('>' in match):
                print('\nWARNING %s %s : possible html tag inside mathjax tags in %s' % (typestr, fname, mathjax_string))

def img_sanity(subpart_dir, container_dir):
    print('Checking container img linking')
    
    # build set of image names from container dir
    container_dir_images = []
    if os.path.exists(os.path.join(container_dir, 'img')):
        for img in os.listdir(os.path.join(container_dir, 'img')):
            container_dir_images.append(os.path.splitext(img)[0])
       
    container_dir_images_set = set(container_dir_images)

    # build set of image names from containers 
    container_images = []
    for container in os.listdir(container_dir):
        if container == 'img':
            continue
        with open(os.path.join(container_dir, container), 'r') as f: 
            container_json = json.load(f)
            extract_images(container_json, container_images, 'container', container)

    container_images_set = set(container_images)

    if (len(container_dir_images) != len(container_images)):
        print('\nWARNING - Length mismatch : dir - %s container - %s' % (container_dir_images, container_images))
    if (container_dir_images_set != container_images_set):
        print('\nElement mismatch : dir - %s container - %s' % (container_dir_images_set, container_images_set))


    print('Done')

    print('Checking subpart img linking')

    # build set of image names from subpart dir
    subpart_dir_images = []
    if (os.path.exists(os.path.join(subpart_dir, 'img'))):
        for img in os.listdir(os.path.join(subpart_dir, 'img')):
            subpart_dir_images.append(os.path.splitext(img)[0])
       
    subpart_dir_images_set = set(subpart_dir_images)

    # build set of image names from containers 
    subpart_images = []
    for subpart in os.listdir(subpart_dir):
        if subpart == 'img':
            continue
        with open(os.path.join(subpart_dir, subpart), 'r') as f: 
            subpart_json = json.load(f)
            extract_images(subpart_json, subpart_images, 'subpart', subpart)

    subpart_images_set = set(subpart_images)

    if (len(subpart_dir_images) != len(subpart_images)):
        print('\nWARNING - Length mismatch : dir - %s subpart - %s' % (subpart_dir_images, subpart_images))
    if (subpart_dir_images_set != subpart_images_set):
        print('\nElement mismatch : dir - %s subpart - %s' % (subpart_dir_images_set, subpart_images_set))

    print('Done')

def extract_images(val, image_list, typestr, fname):
    if isinstance(val, dict):
        for k,v in val.items(): 
            if k == "img":
                if (v[-4:]).lower() == ".png":
                    image_list.append(os.path.splitext(v)[0])
                else:
                    print("%s %s : malformed img value: %s" % (typestr, fname, v))
            else:
                extract_images(v, image_list, typestr, fname)
            
    elif isinstance(val, list):
        for e in val:
            extract_images(e, image_list, typestr, fname)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run basic checks on a chapter's questions")
    parser.add_argument('--target', '-t', required=True, help='path to vault chapter which contains the container and subpart folders')
    parser.add_argument('--html', '-l', action='store_true',help='also perform html validation (this takes a lot of time)')

    processed_args = parser.parse_args()
    print('Running with args: %s' % processed_args)

    check_dir = processed_args.target
    subpart_dir = os.path.join(check_dir, 'subparts')
    container_dir = os.path.join(check_dir, 'containers')

    linking_sanity(subpart_dir, container_dir)
    mathjax_sanity(subpart_dir, container_dir)
    img_sanity(subpart_dir, container_dir)

    if processed_args.html:
        html_sanity(subpart_dir, container_dir)
