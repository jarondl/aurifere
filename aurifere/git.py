import logging
import subprocess
import os
import tempfile
import atexit


logger = logging.getLogger(__name__)


_empty_dir = None
def get_empty_dir():
    global _empty_dir
    if not _empty_dir:
        _empty_dir = tempfile.mkdtemp()
        atexit.register(lambda: os.rmdir(_empty_dir))
    return _empty_dir


class Git:
    def __init__(self, dir):
        self.dir = dir

    def _call(self, args, call_function=subprocess.check_call, **kw):
        try:
            return call_function(args, cwd=self.dir, **kw)
        except subprocess.CalledProcessError:
            logger.info('Exception while excuting command in %s', self.dir)
            raise

    def _git(self, *args):
        """Calls the given git command in the package dir"""
        self._call(('git',) + args)

    def _git_output(self, *args):
        return (self._call(('git',) + args,
                          call_function=subprocess.check_output)
                .decode().strip())

    def init(self):
        """Initializes the git repository"""
        logger.debug("Initializing git repo in %s", self.dir)
        subprocess.check_call(('git', 'init', '--quiet', self.dir,
                               '--template', get_empty_dir()))
        self._git('commit', '--allow-empty', '--quiet', '-m', 'Initial commit')

    def clean(self):
        self._git('clean', '--quiet', '--force')

    def commit_all(self, message):
        self._git('add', '-A')
        self._git('commit', '--quiet', '-m', message)

    def tag(self, tag, force=False):
        # ':' is quite common in version numbers, but not a valid tag
        tag = tag.replace(':', '_')
        if force:
            self._git('tag', '--force', tag)
        else:
            self._git('tag', tag)

    def status(self, untracked_files='no'):
        return self._git_output('status', '--porcelain',
                                '--untracked-files=%s' % untracked_files)

    def switch_branch(self, branch):
        self._git('checkout', branch, '--quiet')

    def ref(self, ref):
        try:
            return self._git_output('show-ref', '--hash', ref)
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                # Ref does not exists
                return None
            raise

    def tag_for_ref(self, ref):
        return self._git_output('describe', '--tags', '--exact-match', ref)
