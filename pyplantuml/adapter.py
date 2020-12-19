import os
import sys

from pylint.config import ConfigurationMixIn

from pylint.pyreverse.inspector import Linker, project_from_files

from pylint.pyreverse.main import Run
from pylint.pyreverse.diadefslib import DiadefsHandler
from pylint.pyreverse.utils import insert_default_options

import pyplantuml.writer as writer

# TODO: Get package arg and add to PATH as well.

class PyreverseAdapter(Run):
    """Integrate with pyreverse by overriding its CLI Run class to
    create diagram definitions that can be passed to a writer."""
    
    def __init__(self, args):
        ConfigurationMixIn.__init__(self, usage=__doc__)
        insert_default_options()
        args = self.load_command_line_configuration()

        sys.exit(self.run(args))

    def run(self, args):
        if not args:
            print(self.help())
            return
        # Insert current working directory to the python path to recognize
        # dependencies to local modules even if cwd is not in the PYTHONPATH.
        sys.path.insert(0, os.getcwd())
        #print(os.getcwd())
        try:
            project = project_from_files(
                args,
                project_name=self.config.project,
                #black_list=self.config.black_list,
            )
            linker = Linker(project, tag=True)
            handler = DiadefsHandler(self.config)
            diadefs = handler.get_diadefs(project, linker)
        finally:
            sys.path.pop(0)

        writer.PlantUmlWriter(self.config).write(diadefs)
        return 0


def getDiagramDefinitions(args):
    """Entry point from outside."""
    return PyreverseAdapter(args).run()
