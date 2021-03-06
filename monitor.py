"""
The MIT License

Copyright (c) 2011 - Dark Secret Software Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import base64
import jinja2
import urllib2
import random
import simplejson
import sys

try:
    import config
except ImportError, e:
    print "Could not import config.py"

keys = ['organization', 'project', 'admin_username', 'admin_password']
missing = [key for key in keys if not hasattr(config, key)]

if missing:
    print "config.py missing:", ",".join(missing)
    sys.exit(1)

organization = config.organization
project = config.project
creds = (config.admin_username, config.admin_password)

open_pulls_url = 'http://github.com/api/v2/json/pulls/%s/%s/open' % \
                                            (organization, project)

# Admin operations - authentication required.
repo_teams = 'http://github.com/api/v2/json/repos/show/%s/%s/teams' % \
                                            (organization, project)

# Ozone is team_id = 34462
team_members = 'http://github.com/api/v2/json/teams/%s/members'


def fetch(url, creds):
    username, password = creds
    req = urllib2.Request(url)
    base = base64.encodestring('%s:%s' % (username, password)
                              ).replace('\n', '')
    req.add_header("Authorization", "Basic %s" % base)
    return simplejson.load(urllib2.urlopen(req))


def get_teams():
    return fetch(repo_teams, creds)['teams']


def get_members(team):
    return fetch(team_members % team['id'], creds)['users']


def remove_duplicate_members(members):
    ids = [member['login'] for member in members]
    unique = list(set(ids))
    added = []
    clean = []
    for member in members:
        if member['login'] not in added:
            clean.append(member)
            added.append(member['login'])
    return clean


def get_open_pulls():
    return fetch(open_pulls_url, creds)['pulls']


teams = get_teams()
members = []
for team in teams:
    members.extend(get_members(team))
members = remove_duplicate_members(members)
names = [member['login'] for member in members]
approvers = ', '.join(names)

open_pulls = get_open_pulls()
# fake some states
states = ['Needs Review', 'WIP', 'Jenkins', 'Approved']
for pull in open_pulls:
    # some fake votes ...
    core = random.randrange(5)
    non_core = random.randrange(5)
    needs_fixing = random.randrange(5)
    rejected = random.randrange(5)

    pull['workflow_core'] = core
    pull['workflow_non_core'] = non_core
    pull['workflow_needs_fixing'] = needs_fixing
    pull['workflow_rejected'] = rejected
    pull['workflow'] = random.choice(states)

context = dict(pulls = open_pulls,
               approvers = approvers,
               organization = organization,
               project = project,
               project_home = 'https://github.com/%s/%s' %
                              (organization, project))

env = jinja2.Environment(loader = jinja2.FileSystemLoader('.'))
template = env.get_template("template.html")
output = template.render(context)

with open('index.html', 'w') as f:
    f.write(output)
