# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Portions Copyright (C) Philipp Kewisch, 2013

import os
import sys
import json
import datetime
import re
import string

from .config import config

try:
  import git
  gitSupport = True
except:
  gitSupport = False

ISSUE_RE = re.compile(r"[A-Z]+-\d+")

def json_pp(obj):
  return json.dumps(obj, sort_keys=True, indent=2, separators=(',', ': '))

def textOptions(kv):
  optprompt = []
  opts = {}
  for s,v in kv.items():
    x = 0
    while x < len(s) and s[x] in string.ascii_letters and s[x].lower() in opts:
      x += 1

    if x == len(s) or s[x] not in string.ascii_letters:
      # couldn't find a letter, use whole string
      opts[s.lower()] = v
    else:
      # use first found letter
      opts[s[x].lower()] = v
      s = s[:x] + ("(%s)" % s[x]) + s[x+1:]
    optprompt.append(s)

  return opts,", ".join(optprompt)

def isonow(delta=None):
  dtnow = datetime.datetime.now()
  utcnow = datetime.datetime.utcnow()

  if delta:
    dtnow += delta
    utcnow += delta

  delta = dtnow - utcnow
  hh,mm = divmod((delta.days * 86400 + delta.seconds + 30) // 60, 60)
  return "%s%+03d:%02d" % (dtnow.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3], hh, mm)


def gitroot(path):
  while not path == "/":
    if os.path.exists(os.path.join(path, ".git")):
      return path
    path = os.path.dirname(path)
  return None


def isPlaceholder(placeholder):
  return placeholder in ["@","_"]

def translatePlaceholder(placeholder, asReview=False):
    issue = None
    if placeholder == "_":
      issue = config.get("cache", "lastissue")
      if issue is not  None:
        print("Using last issue %s" % issue)
    elif placeholder == "@" and gitSupport:
      root = gitroot(os.getcwd())
      repo = git.Repo(root)
      branch = repo.active_branch.name
      issueMatch = ISSUE_RE.search(branch)
      if issueMatch is not None:
        issue = issueMatch.group(0)
        print("Using issue %s from git branch" % issue)
    return issue


def getRepoProps(head=None):
  root = gitroot(os.getcwd())
  gitrepo = git.Repo(root)

  if head is None:
    head = gitrepo.active_branch.name

  config = gitrepo.heads[head].config_reader()
  remote = config.get_value("remote", default="origin")
  ref = config.get_value("merge", default="refs/heads/%s" % head) or None
  url = gitrepo.remotes[remote].config_reader.get_value("url", default=None)

  parts = url.split("/")
  project = parts[-2]
  repo = parts[-1].replace(".git", "")

  return project,repo,ref,url

def untangleProject(project):
  _,username = os.path.split(project)
  userpath = os.path.expanduser("~" + username)
  if project.startswith(userpath):
    project = "~" + username
  return project
