#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import glob
import json
import mimetypes
import os
import re
import shutil
import subprocess
import tempfile
from six.moves.urllib.parse import urlparse

import boto3
import botocore
import yattag


class Bucket(object):
    def __init__(self, url):
        if not re.match(r'^(s3:)?//', url):
            url = '//' + url
        url = urlparse(url)
        self.name = url.netloc
        self.prefix = url.path.lstrip('/')
        self.s3_client = boto3.client('s3')
        self.s3 = boto3.resource('s3')
        self.bucket = self.s3.Bucket(self.name)

    def has_key(self, key):
        try:
            print(self.s3.Object(self.name, os.path.join(self.prefix, key)))
            self.s3.Object(self.name, os.path.join(self.prefix, key)).load()
        except botocore.exceptions.ClientError as e:
            return False
        return True

    def generate_url(self, key):
        index_url = self.s3_client.generate_presigned_url('get_object', Params={'Bucket': "careerleaf-wheelhouse",
                                                            'Key': key},)
        return index_url.split('?')[0]

    def list(self):
        client = boto3.client('s3')
        return client.list_objects( Bucket=self.name, Prefix=self.prefix )['Contents']

    def sync(self, local_dir):
        return subprocess.check_call([
            'aws', 's3', 'sync',
            local_dir, 's3://{0}/{1}'.format(self.name, self.prefix),
            '--region', 'us-east-1'])

    def put(self, file, key, type=None):
        content_type = mimetypes.guess_type(file)[0]
        self.bucket.upload_file(file, os.path.join(self.prefix, key),ExtraArgs={
        'ContentType': content_type, 'ACL': 'public-read',})

    def list_wheels(self):
        return [key['Key'] for key in self.list() if key['Key'].endswith('.whl')]

    def make_index(self):
        doc, tag, text = yattag.Doc().tagtext()
        with tag('html'):
            for key in self.list_wheels():
                with tag('a', href=self.generate_url(key)):
                    text(key)
                doc.stag('br')
        return doc.getvalue()


def build_wheels(packages, index_url, requirements, exclusions):
    temp_dir = tempfile.mkdtemp(prefix='mkwheelhouse-')

    args = [
        'pip', 'wheel',
        '--wheel-dir', temp_dir,
        '--find-links', index_url,
        '--no-cache-dir'
    ]

    for requirement in requirements:
        args += ['--requirement', requirement]

    args += packages
    subprocess.check_call(args)

    for exclusion in exclusions:
        matches = glob.glob(os.path.join(temp_dir, exclusion))
        for match in matches:
            os.remove(match)

    return temp_dir


def main():
    parser = argparse.ArgumentParser(
        description='Generate and upload wheels to an Amazon S3 wheelhouse')
    parser.add_argument('-r', '--requirement', action='append', default=[],
                        metavar='REQUIREMENTS_FILE',
                        help='Requirements file to build wheels for')
    parser.add_argument('-e', '--exclude', action='append', default=[],
                        metavar='WHEEL_FILENAME',
                        help='Wheels to exclude from upload')
    parser.add_argument('bucket')
    parser.add_argument('package', nargs='*', default=[])

    args = parser.parse_args()
    print(args.package)
    if not args.requirement and not args.package:
        parser.error('specify at least one requirements file or package')

    bucket = Bucket(args.bucket)
    file=open("index.html",'w')
    file.write('<!DOCTYPE html><html></html>')
    if not bucket.has_key('index.html'):
        bucket.put('index.html',key='index.html')
    file=open("index.html",'w')
    index_url = bucket.generate_url("%s/index.html"%(bucket.prefix))

    build_dir = build_wheels(args.package, index_url, args.requirement, args.exclude)
    bucket.sync(build_dir)
    file.write(bucket.make_index())
    file.close()
    bucket.put('index.html', key='index.html')
    shutil.rmtree(build_dir)
    print('Index written to:', index_url)

if __name__ == '__main__':
    main()
