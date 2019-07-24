"""Rule Generator for Forseti's Lien Scanner.

Creates global rules to require project deletion lien for all projects.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from deploy.rule_generator.scanners import base_scanner_rules


class LienScannerRules(base_scanner_rules.BaseScannerRules):
  """Scanner rule generator for the Lien scanner."""

  def config_file_name(self):
    return 'lien_rules.yaml'

  def _get_global_rules(self, global_config, project_configs):
    return [{
        'name': 'Require project deletion liens for all projects.',
        'mode': 'required',
        'resource': self._get_resources(global_config, project_configs),
        'restrictions': ['resourcemanager.projects.delete'],
    }]
