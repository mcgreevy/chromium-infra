# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from infra.libs import git2
from infra.libs.git2.test import test_util


class TestCommit(test_util.TestBasis):
  def testComparison(self):
    r = self.mkRepo()
    c = r['refs/heads/branch_O'].commit
    self.assertEqual(c, c)
    self.assertEqual(c, r['refs/heads/branch_O'].commit)
    self.assertNotEqual(c, r['refs/heads/branch_S'].commit)
    self.assertIs(c.repo, r)

  def testRepr(self):
    r = self.mkRepo()
    c = r['refs/heads/branch_O'].commit
    self.assertEqual("Commit(%r, %r)" % (r, self.repo['O']), repr(c))

  def testData(self):
    r = self.mkRepo()
    d = r['refs/heads/branch_O'].commit.data
    self.assertEqual(d.committer.email, 'commitish@example.com')

  def testBogus(self):
    r = self.mkRepo()
    d = git2.Commit(r, 'deadbeefdeadbeefdeadbeefdeadbeefdeadbeef').data
    self.assertIs(d, git2.INVALID)
    self.assertIs(d.committer, git2.INVALID)
    self.assertIs(d.committer.alter(user='tom'), git2.INVALID)

  def testParent(self):
    r = self.mkRepo()
    c = r['refs/heads/branch_O'].commit
    self.assertEqual(c.parent.hsh, self.repo['N'])

    a = r['refs/heads/root_A'].commit
    self.assertIsNone(a.parent)

    z = r['refs/heads/branch_Z'].commit
    self.assertIs(z.parent, git2.INVALID)

  def testAlter(self):
    r = self.mkRepo()
    c = r['refs/heads/branch_O'].commit
    d = c.data

    a = c.alter(committer=d.committer.alter(email='bob@dude.example.com'))
    self.assertEqual(a.hsh, 'fadfbe63d40f60f5313a71a1c9d72a741ee91770')

    with self.assertRaises(Exception):
      c.alter(tree='failbeef')

