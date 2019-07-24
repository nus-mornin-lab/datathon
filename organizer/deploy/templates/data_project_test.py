# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for healthcare.deploy.templates.data_project.

These tests check that the template is free from syntax errors and generates
the expected resources.

To run tests, run `python -m unittest tests.data_project_test` from the
templates directory.
"""

from absl.testing import absltest

from deploy.templates import data_project


class TestDataProject(absltest.TestCase):

  def test_expansion_local_logging(self):

    class FakeContext(object):
      env = {
          'deployment': 'my-deployment',
          'project': 'my-project',
      }
      properties = {
          'has_organization':
              True,
          'remove_owner_user':
              'some-owner@mydomain.com',
          'owners_group':
              'some-admin-group@googlegroups.com',
          'auditors_group':
              'some-aud-group@googlegroups.com',
          'data_readwrite_groups': [
              'some-rw-group@googlegroups.com',
              'another-rw-group@googlegroups.com',
          ],
          'data_readonly_groups': [
              'some-r-group@googlegroups.com',
              'another-r-group@googlegroups.com',
          ],
          'custom_roles': [
              {
                  'name': 'bucketLister',
                  'permissions': ['storage.buckets.list'],
                  'title': 'The title of bucketLister',
                  'description': 'The description of bucketLister'
              },
              {
                  'name':
                      'dataflow_runner',
                  'permissions': [
                      'bigquery.datasets.create', 'bigquery.jobs.create'
                  ],
              },
          ],
          'local_audit_logs': {
              'logs_gcs_bucket': {
                  'location': 'US',
                  'storage_class': 'MULTI_REGIONAL',
                  'ttl_days': 365,
              },
              'logs_bigquery_dataset': {
                  'location': 'US',
              },
          },
          'bigquery_datasets': [
              {
                  'name': 'us_data',
                  'location': 'US',
                  'additional_dataset_permissions': {
                      'owners': ['user:some-bq-owner1@domain.com,'],
                      'readonly': [
                          'allAuthenticatedUsers', 'domain:some-bq-domain.com'
                      ],
                      'readwrite': [
                          'group:some-bq-readwrite1@domain.com,',
                          'serviceAccount:some-bq-service@g.com'
                      ]
                  }
              },
              {
                  'name': 'euro_data',
                  'location': 'EU',
              },
          ],
          'data_buckets': [
              {
                  'name':
                      'my-project-nlp-bucket',
                  'location':
                      'US-CENTRAL1',
                  'storage_class':
                      'REGIONAL',
                  'additional_bucket_permissions': {
                      'owners': ['group:bucket-owner-group@domain.com,'],
                      'readwrite': [
                          'group:bucket-readwrite-group@domain.com,',
                          'serviceAccount:2559@anser.anaccnt.com',
                          'allAuthenticatedUsers'
                      ],
                      'writeonly': ['group:bucket-writeonly-group@domain.com,'],
                      'readonly': [
                          'group:bucket-readonly-group1@domain.com,',
                          'group:bucket-readonly-group2@domain.com,',
                          'domain:domain.com,', 'allUsers'
                      ]
                  },
                  'expected_users': [
                      'auth_user_1@mydomain.com',
                      'auth_user_2@mydomain.com',
                  ],
              },
              {
                  'name': 'my-project-other-bucket',
                  'location': 'US-EAST1',
                  'storage_class': 'REGIONAL',
              },
              {
                  'name': 'my-project-euro-bucket',
                  'location': 'EUROPE-WEST1',
                  'storage_class': 'REGIONAL',
                  'expected_users': ['auth_user_3@mydomain.com'],
              },
          ],
          'pubsub': {
              'topic': 'test-topic',
              'subscription': 'test-subscription',
              'publisher_account':
                  ('cloud-healthcare-eng@system.gserviceaccount.com'),
              'ack_deadline_sec': 100
          },
          'enabled_apis': [
              'cloudbuild.googleapis.com',
              'cloudresourcemanager.googleapis.com',  # Ignored by script.
              'containerregistry.googleapis.com',
              'deploymentmanager.googleapis.com',  # Ignored by script.
          ]
      }

    generated = data_project.generate_config(FakeContext())

    expected = {
        'resources': [
            {
                'name': 'bucketLister',
                'type': 'gcp-types/iam-v1:projects.roles',
                'properties': {
                    'parent': 'projects/my-project',
                    'roleId': 'bucketLister',
                    'role': {
                        'title': 'The title of bucketLister',
                        'description': 'The description of bucketLister',
                        'stage': 'GA',
                        'includedPermissions': ['storage.buckets.list'],
                    },
                },
            },
            {
                'name': 'dataflow_runner',
                'type': 'gcp-types/iam-v1:projects.roles',
                'properties': {
                    'parent': 'projects/my-project',
                    'roleId': 'dataflow_runner',
                    'role': {
                        'title':
                            'dataflow_runner',
                        'description':
                            'dataflow_runner',
                        'stage':
                            'GA',
                        'includedPermissions': [
                            'bigquery.datasets.create', 'bigquery.jobs.create'
                        ],
                    },
                }
            },
            {
                'name': 'set-project-bindings-get-iam-policy',
                'action': ('gcp-types/cloudresourcemanager-v1:'
                           'cloudresourcemanager.projects.getIamPolicy'),
                'properties': {
                    'resource': 'my-project'
                },
                'metadata': {
                    'runtimePolicy': ['UPDATE_ALWAYS']
                },
            },
            {
                'name': 'set-project-bindings-patch-iam-policy',
                'action': ('gcp-types/cloudresourcemanager-v1:'
                           'cloudresourcemanager.projects.setIamPolicy'),
                'properties': {
                    'resource': 'my-project',
                    'policy': '$(ref.set-project-bindings-get-iam-policy)',
                    'gcpIamPolicyPatch': {
                        'add':
                            [{
                                'role':
                                    'roles/iam.securityReviewer',
                                'members': [
                                    'group:some-aud-group@googlegroups.com'
                                ],
                            },
                             {
                                 'role':
                                     'roles/owner',
                                 'members': [
                                     'group:some-admin-group@googlegroups.com'
                                 ],
                             }],
                        'remove': [{
                            'role': 'roles/owner',
                            'members': ['user:some-owner@mydomain.com'],
                        }],
                    },
                },
                'metadata': {
                    'runtimePolicy': ['UPDATE_ON_CHANGE'],
                },
            },
            {
                'name': 'my-project-logs',
                'type': 'storage.v1.bucket',
                'accessControl': {
                    'gcpIamPolicy': {
                        'bindings':
                            [{
                                'role':
                                    'roles/storage.admin',
                                'members': [
                                    'group:some-admin-group@googlegroups.com'
                                ],
                            },
                             {
                                 'role':
                                     'roles/storage.objectViewer',
                                 'members': [
                                     'group:some-aud-group@googlegroups.com'
                                 ]
                             },
                             {
                                 'role':
                                     'roles/storage.objectCreator',
                                 'members': [
                                     'group:cloud-storage-analytics@google.com'
                                 ]
                             }]
                    }
                },
                'properties': {
                    'location': 'US',
                    'storageClass': 'MULTI_REGIONAL',
                    'lifecycle': {
                        'rule': [{
                            'action': {
                                'type': 'Delete'
                            },
                            'condition': {
                                'isLive': True,
                                'age': 365
                            }
                        }]
                    }
                }
            },
            {
                'name': 'audit-logs-to-bigquery',
                'type': 'logging.v2.sink',
                'properties': {
                    'sink': 'audit-logs-to-bigquery',
                    'uniqueWriterIdentity': True,
                    'destination': (
                        'bigquery.googleapis.com/projects/my-project/'
                        'datasets/audit_logs'),
                    'filter': 'logName:"logs/cloudaudit.googleapis.com"',
                }
            },
            {
                'name': 'create-big-query-dataset-us_data',
                'type': 'bigquery.v2.dataset',
                'properties': {
                    'datasetReference': {
                        'datasetId': 'us_data'
                    },
                    'location': 'US',
                },
            },
            {
                'name': 'update-big-query-dataset-us_data',
                'action': 'gcp-types/bigquery-v2:bigquery.datasets.patch',
                'properties': {
                    'projectId':
                        'my-project',
                    'datasetId':
                        'us_data',
                    'access': [
                        {
                            'role': 'OWNER',
                            'groupByEmail': 'some-admin-group@googlegroups.com',
                        },
                        {
                            'role': 'READER',
                            'groupByEmail': 'some-r-group@googlegroups.com',
                        },
                        {
                            'role': 'READER',
                            'groupByEmail': 'another-r-group@googlegroups.com',
                        },
                        {
                            'role': 'WRITER',
                            'groupByEmail': 'some-rw-group@googlegroups.com',
                        },
                        {
                            'role': 'WRITER',
                            'groupByEmail': 'another-rw-group@googlegroups.com',
                        },
                        {
                            'role': 'OWNER',
                            'userByEmail': 'some-bq-owner1@domain.com,',
                        },
                        {
                            'role': 'WRITER',
                            'groupByEmail': 'some-bq-readwrite1@domain.com,',
                        },
                        {
                            'role': 'WRITER',
                            'userByEmail': 'some-bq-service@g.com',
                        },
                        {
                            'role': 'READER',
                            'specialGroup': 'allAuthenticatedUsers',
                        }, {
                            'role': 'READER',
                            'domain': 'some-bq-domain.com',
                        }
                    ],
                },
                'metadata': {
                    'dependsOn': ['create-big-query-dataset-us_data'],
                    'runtimePolicy': ['UPDATE_ON_CHANGE'],
                },
            },
            {
                'name': 'create-big-query-dataset-euro_data',
                'type': 'bigquery.v2.dataset',
                'properties': {
                    'datasetReference': {
                        'datasetId': 'euro_data'
                    },
                    'location': 'EU',
                },
                'metadata': {
                    'dependsOn': ['update-big-query-dataset-us_data']
                },
            },
            {
                'name': 'update-big-query-dataset-euro_data',
                'action': 'gcp-types/bigquery-v2:bigquery.datasets.patch',
                'properties': {
                    'projectId':
                        'my-project',
                    'datasetId':
                        'euro_data',
                    'access': [
                        {
                            'role': 'OWNER',
                            'groupByEmail': 'some-admin-group@googlegroups.com',
                        },
                        {
                            'role': 'READER',
                            'groupByEmail': 'some-r-group@googlegroups.com',
                        },
                        {
                            'role': 'READER',
                            'groupByEmail': 'another-r-group@googlegroups.com',
                        },
                        {
                            'role': 'WRITER',
                            'groupByEmail': 'some-rw-group@googlegroups.com',
                        },
                        {
                            'role': 'WRITER',
                            'groupByEmail': 'another-rw-group@googlegroups.com',
                        }
                    ],
                },
                'metadata': {
                    'dependsOn': ['create-big-query-dataset-euro_data'],
                    'runtimePolicy': ['UPDATE_ON_CHANGE'],
                },
            },
            {
                'name': 'my-project-nlp-bucket',
                'type': 'storage.v1.bucket',
                'metadata': {
                    'dependsOn': ['my-project-logs']
                },
                'accessControl': {
                    'gcpIamPolicy': {
                        'bindings':
                            [{
                                'role':
                                    'roles/storage.admin',
                                'members': [
                                    'group:some-admin-group@googlegroups.com',
                                    'group:bucket-owner-group@domain.com,'
                                ]
                            },
                             {
                                 'role':
                                     'roles/storage.objectAdmin',
                                 'members': [
                                     'group:some-rw-group@googlegroups.com',
                                     'group:another-rw-group@googlegroups.com',
                                     'group:bucket-readwrite-group@domain.com,',
                                     'serviceAccount:2559@anser.anaccnt.com',
                                     'allAuthenticatedUsers'
                                 ]
                             },
                             {
                                 'role':
                                     'roles/storage.objectViewer',
                                 'members': [
                                     'group:some-r-group@googlegroups.com',
                                     'group:another-r-group@googlegroups.com',
                                     'group:bucket-readonly-group1@domain.com,',
                                     'group:bucket-readonly-group2@domain.com,',
                                     'domain:domain.com,', 'allUsers'
                                 ]
                             },
                             {
                                 'role':
                                     'roles/storage.objectCreator',
                                 'members': [
                                     'group:bucket-writeonly-group@domain.com,'
                                 ]
                             }]
                    }
                },
                'properties': {
                    'location': 'US-CENTRAL1',
                    'versioning': {
                        'enabled': True
                    },
                    'storageClass': 'REGIONAL',
                    'logging': {
                        'logBucket': 'my-project-logs'
                    }
                }
            },
            {
                'name': 'unexpected-access-my-project-nlp-bucket',
                'type': 'logging.v2.metric',
                'properties': {
                    'filter': (
                        'resource.type=gcs_bucket AND '
                        'logName=projects/my-project/logs/'
                        'cloudaudit.googleapis.com%2Fdata_access AND '
                        'protoPayload.resourceName=projects/_/buckets/'
                        'my-project-nlp-bucket AND '
                        'protoPayload.status.code!=7 AND '
                        'protoPayload.authenticationInfo.principalEmail!=('
                        'auth_user_1@mydomain.com AND '
                        'auth_user_2@mydomain.com)'),
                    'description': 'Count of unexpected data access to '
                                   'my-project-nlp-bucket.',
                    'labelExtractors': {
                        'user': (
                            'EXTRACT('
                            'protoPayload.authenticationInfo.principalEmail)'),
                    },
                    'metricDescriptor': {
                        'labels': [{
                            'description': 'Unexpected user',
                            'key': 'user',
                            'valueType': 'STRING'
                        }],
                        'unit': '1',
                        'metricKind': 'DELTA',
                        'valueType': 'INT64'
                    },
                    'metric': 'unexpected-access-my-project-nlp-bucket'
                }
            },
            {
                'name': 'my-project-other-bucket',
                'type': 'storage.v1.bucket',
                'metadata': {
                    'dependsOn': ['my-project-nlp-bucket']
                },
                'accessControl': {
                    'gcpIamPolicy': {
                        'bindings': [
                            {
                                'role':
                                    'roles/storage.admin',
                                'members': [
                                    'group:some-admin-group@googlegroups.com'
                                ]
                            },
                            {
                                'role':
                                    'roles/storage.objectAdmin',
                                'members': [
                                    'group:some-rw-group@googlegroups.com',
                                    'group:another-rw-group@googlegroups.com',
                                ]
                            },
                            {
                                'role':
                                    'roles/storage.objectViewer',
                                'members': [
                                    'group:some-r-group@googlegroups.com',
                                    'group:another-r-group@googlegroups.com',
                                ]
                            }
                        ]
                    }
                },
                'properties': {
                    'location': 'US-EAST1',
                    'versioning': {
                        'enabled': True
                    },
                    'storageClass': 'REGIONAL',
                    'logging': {
                        'logBucket': 'my-project-logs'
                    }
                }
            },
            {
                'name': 'my-project-euro-bucket',
                'type': 'storage.v1.bucket',
                'metadata': {
                    'dependsOn': ['my-project-other-bucket']
                },
                'accessControl': {
                    'gcpIamPolicy': {
                        'bindings': [
                            {
                                'role':
                                    'roles/storage.admin',
                                'members': [
                                    'group:some-admin-group@googlegroups.com'
                                ]
                            },
                            {
                                'role':
                                    'roles/storage.objectAdmin',
                                'members': [
                                    'group:some-rw-group@googlegroups.com',
                                    'group:another-rw-group@googlegroups.com',
                                ]
                            },
                            {
                                'role':
                                    'roles/storage.objectViewer',
                                'members': [
                                    'group:some-r-group@googlegroups.com',
                                    'group:another-r-group@googlegroups.com',
                                ]
                            }
                        ]
                    }
                },
                'properties': {
                    'location': 'EUROPE-WEST1',
                    'versioning': {
                        'enabled': True
                    },
                    'storageClass': 'REGIONAL',
                    'logging': {
                        'logBucket': 'my-project-logs'
                    }
                }
            },
            {
                'name': 'unexpected-access-my-project-euro-bucket',
                'type': 'logging.v2.metric',
                'properties': {
                    'filter': (
                        'resource.type=gcs_bucket AND '
                        'logName=projects/my-project/logs/'
                        'cloudaudit.googleapis.com%2Fdata_access AND '
                        'protoPayload.resourceName=projects/_/buckets/'
                        'my-project-euro-bucket AND '
                        'protoPayload.status.code!=7 AND '
                        'protoPayload.authenticationInfo.principalEmail!=('
                        'auth_user_3@mydomain.com)'),
                    'description': ('Count of unexpected data access to '
                                    'my-project-euro-bucket.'),
                    'labelExtractors': {
                        'user': (
                            'EXTRACT('
                            'protoPayload.authenticationInfo.principalEmail)'),
                    },
                    'metricDescriptor': {
                        'labels': [{
                            'description': 'Unexpected user',
                            'key': 'user',
                            'valueType': 'STRING'
                        }],
                        'unit': '1',
                        'metricKind': 'DELTA',
                        'valueType': 'INT64'
                    },
                    'metric': 'unexpected-access-my-project-euro-bucket'
                }
            },
            {
                'name': 'test-topic',
                'type': 'pubsub.v1.topic',
                'properties': {
                    'topic': 'test-topic',
                },
                'accessControl': {
                    'gcpIamPolicy': {
                        'bindings': [{
                            'role':
                                'roles/pubsub.publisher',
                            'members': [('serviceAccount:cloud-healthcare-eng'
                                         '@system.gserviceaccount.com')],
                        },],
                    },
                },
            },
            {
                'name': 'test-subscription',
                'type': 'pubsub.v1.subscription',
                'properties': {
                    'subscription': 'test-subscription',
                    'topic': 'projects/my-project/topics/test-topic',
                    'ackDeadlineSeconds': 100,
                },
                'accessControl': {
                    'gcpIamPolicy': {
                        'bindings': [{
                            'role':
                                'roles/pubsub.editor',
                            'members': [
                                'group:some-rw-group@googlegroups.com',
                                ('group:another-rw-group@googlegroups.'
                                 'com'),
                            ],
                        }],
                    },
                },
                'metadata': {
                    'dependsOn': ['test-topic'],
                },
            },
            {
                'name': 'iam-policy-change-count',
                'type': 'logging.v2.metric',
                'properties': {
                    'filter': ('protoPayload.methodName="SetIamPolicy" OR\n'
                               'protoPayload.methodName:".setIamPolicy"'),
                    'description': 'Count of IAM policy changes.',
                    'labelExtractors': {
                        'user': (
                            'EXTRACT('
                            'protoPayload.authenticationInfo.principalEmail)'),
                    },
                    'metricDescriptor': {
                        'labels': [{
                            'description': 'Unexpected user',
                            'key': 'user',
                            'valueType': 'STRING'
                        }],
                        'unit': '1',
                        'metricKind': 'DELTA',
                        'valueType': 'INT64'
                    },
                    'metric': 'iam-policy-change-count'
                }
            },
            {
                'name': 'bucket-permission-change-count',
                'type': 'logging.v2.metric',
                'properties': {
                    'filter': (
                        '\n      resource.type=gcs_bucket AND\n      '
                        'protoPayload.serviceName=storage.googleapis.com AND\n'
                        '      '
                        '(protoPayload.methodName=storage.setIamPermissions '
                        'OR\n       '
                        'protoPayload.methodName=storage.objects.update)'),
                    'description': 'Count of GCS permissions changes.',
                    'labelExtractors': {
                        'user': (
                            'EXTRACT('
                            'protoPayload.authenticationInfo.principalEmail)'),
                    },
                    'metricDescriptor': {
                        'labels': [{
                            'description': 'Unexpected user',
                            'key': 'user',
                            'valueType': 'STRING'
                        }],
                        'unit': '1',
                        'metricKind': 'DELTA',
                        'valueType': 'INT64'
                    },
                    'metric': 'bucket-permission-change-count'
                }
            },
            {
                'name': 'bigquery-settings-change-count',
                'type': 'logging.v2.metric',
                'properties': {
                    'filter': (
                        'resource.type="bigquery_resource" AND\n'
                        'protoPayload.methodName="datasetservice.update"'),
                    'description': 'Count of bigquery permission changes.',
                    'labelExtractors': {
                        'user': (
                            'EXTRACT('
                            'protoPayload.authenticationInfo.principalEmail)'),
                    },
                    'metricDescriptor': {
                        'labels': [{
                            'description': 'Unexpected user',
                            'key': 'user',
                            'valueType': 'STRING'
                        }],
                        'unit': '1',
                        'metricKind': 'DELTA',
                        'valueType': 'INT64'
                    },
                    'metric': 'bigquery-settings-change-count'
                }
            },
            {
                'name': 'audit-configs-get-iam-etag',
                'action': ('gcp-types/cloudresourcemanager-v1:'
                           'cloudresourcemanager.projects.getIamPolicy'),
                'properties': {
                    'resource': 'my-project',
                },
                'metadata': {
                    'runtimePolicy': ['UPDATE_ALWAYS'],
                    'dependsOn': ['set-project-bindings-patch-iam-policy'],
                },
            },
            {
                'name': 'audit-configs-patch-iam-policy',
                'action': ('gcp-types/cloudresourcemanager-v1:'
                           'cloudresourcemanager.projects.setIamPolicy'),
                'properties': {
                    'updateMask': 'auditConfigs,etag',
                    'resource': 'my-project',
                    'policy': {
                        'auditConfigs': [{
                            'auditLogConfigs': [
                                {
                                    'logType': 'ADMIN_READ'
                                },
                                {
                                    'logType': 'DATA_WRITE'
                                },
                                {
                                    'logType': 'DATA_READ'
                                },
                            ],
                            'service': 'allServices',
                        }],
                        'etag': '$(ref.audit-configs-get-iam-etag.etag)',
                    },
                },
                'metadata': {
                    'dependsOn': ['audit-configs-get-iam-etag'],
                    'runtimePolicy': ['UPDATE_ON_CHANGE'],
                },
            },
        ]
    }

    index = 0
    self.assertLen(generated['resources'], len(expected['resources']))
    while index < len(generated['resources']):
      self.assertEqual(generated['resources'][index],
                       expected['resources'][index])
      index += 1

  def testExpansionRemoteLoggingNoOrg(self):

    class FakeContext(object):
      env = {
          'deployment': 'my-deployment',
          'project': 'my-project',
      }
      properties = {
          'has_organization':
              False,
          'owners_group':
              'some-admin-group@googlegroups.com',
          'editors_group':
              'some-editors-group@googlegroups.com',
          'auditors_group':
              'some-aud-group@googlegroups.com',
          'additional_project_permissions': [
              {
                  'roles': ['roles/editor',],
                  'members': [
                      'serviceAccount:s1234@service.accounts',
                      'serviceAccount:s5678@service.accounts'
                  ]
              },
              {
                  'roles': [
                      'roles/bigquery.dataViewer', 'roles/storage.objectViewer'
                  ],
                  'members': [
                      'group:extra-viewers@googlegroups.com',
                      'user:some-viewer@mydomain.com'
                  ]
              },
          ],
          'data_readwrite_groups': ['some-rw-group@googlegroups.com'],
          'data_readonly_groups': ['some-r-group@googlegroups.com'],
          'remote_audit_logs': {
              'audit_logs_project_id': 'my-audit-logs',
              'logs_gcs_bucket_name': 'some_remote_bucket',
              'logs_bigquery_dataset_id': 'some_remote_dataset',
          },
          'bigquery_datasets': [{
              'name': 'us_data',
              'location': 'US',
          },],
          'data_buckets': [{
              'name': 'my-project-data',
              'location': 'US',
              'storage_class': 'MULTI_REGIONAL',
          },],
      }

    generated = data_project.generate_config(FakeContext())

    expected = {
        'resources': [
            {
                'name': 'set-project-bindings-get-iam-policy',
                'action': ('gcp-types/cloudresourcemanager-v1:'
                           'cloudresourcemanager.projects.getIamPolicy'),
                'properties': {
                    'resource': 'my-project'
                },
                'metadata': {
                    'runtimePolicy': ['UPDATE_ALWAYS']
                },
            },
            {
                'name': 'set-project-bindings-patch-iam-policy',
                'action': ('gcp-types/cloudresourcemanager-v1:'
                           'cloudresourcemanager.projects.setIamPolicy'),
                'properties': {
                    'resource': 'my-project',
                    'policy': '$(ref.set-project-bindings-get-iam-policy)',
                    'gcpIamPolicyPatch': {
                        'add': [
                            {
                                'role':
                                    'roles/bigquery.dataViewer',
                                'members': [
                                    'group:extra-viewers@googlegroups.com',
                                    'user:some-viewer@mydomain.com',
                                ],
                            },
                            {
                                'role':
                                    'roles/editor',
                                'members': [
                                    'group:some-editors-group@googlegroups.com',
                                    'serviceAccount:s1234@service.accounts',
                                    'serviceAccount:s5678@service.accounts',
                                ],
                            },
                            {
                                'role':
                                    'roles/iam.securityReviewer',
                                'members': [
                                    'group:some-aud-group@googlegroups.com',
                                ],
                            },
                            {
                                'role':
                                    'roles/resourcemanager.projectIamAdmin',
                                'members': [
                                    'group:some-admin-group@googlegroups.com',
                                ],
                            },
                            {
                                'role':
                                    'roles/storage.objectViewer',
                                'members': [
                                    'group:extra-viewers@googlegroups.com',
                                    'user:some-viewer@mydomain.com',
                                ],
                            },
                        ],
                    },
                },
                'metadata': {
                    'runtimePolicy': ['UPDATE_ON_CHANGE'],
                },
            },
            {
                'name': 'audit-logs-to-bigquery',
                'type': 'logging.v2.sink',
                'properties': {
                    'sink': 'audit-logs-to-bigquery',
                    'uniqueWriterIdentity': True,
                    'destination': (
                        'bigquery.googleapis.com/projects/'
                        'my-audit-logs/datasets/some_remote_dataset'),
                    'filter': 'logName:"logs/cloudaudit.googleapis.com"',
                }
            },
            {
                'name': 'create-big-query-dataset-us_data',
                'type': 'bigquery.v2.dataset',
                'properties': {
                    'datasetReference': {
                        'datasetId': 'us_data'
                    },
                    'location': 'US',
                },
            },
            {
                'name': 'update-big-query-dataset-us_data',
                'action': 'gcp-types/bigquery-v2:bigquery.datasets.patch',
                'properties': {
                    'projectId':
                        'my-project',
                    'datasetId':
                        'us_data',
                    'access': [{
                        'role': 'OWNER',
                        'groupByEmail': 'some-admin-group@googlegroups.com',
                    },
                               {
                                   'role':
                                       'READER',
                                   'groupByEmail':
                                       'some-r-group@googlegroups.com',
                               },
                               {
                                   'role':
                                       'WRITER',
                                   'groupByEmail':
                                       'some-rw-group@googlegroups.com',
                               }],
                },
                'metadata': {
                    'dependsOn': ['create-big-query-dataset-us_data'],
                    'runtimePolicy': ['UPDATE_ON_CHANGE'],
                },
            },
            {
                'name': 'my-project-data',
                'type': 'storage.v1.bucket',
                'accessControl': {
                    'gcpIamPolicy': {
                        'bindings':
                            [{
                                'role':
                                    'roles/storage.admin',
                                'members': [
                                    'group:some-admin-group@googlegroups.com'
                                ]
                            },
                             {
                                 'role':
                                     'roles/storage.objectAdmin',
                                 'members': [
                                     'group:some-rw-group@googlegroups.com'
                                 ]
                             },
                             {
                                 'role':
                                     'roles/storage.objectViewer',
                                 'members': [
                                     'group:some-r-group@googlegroups.com'
                                 ]
                             }]
                    }
                },
                'properties': {
                    'location': 'US',
                    'versioning': {
                        'enabled': True
                    },
                    'storageClass': 'MULTI_REGIONAL',
                    'logging': {
                        'logBucket': 'some_remote_bucket'
                    }
                },
            },
            {
                'name': 'iam-policy-change-count',
                'type': 'logging.v2.metric',
                'properties': {
                    'filter': ('protoPayload.methodName="SetIamPolicy" OR\n'
                               'protoPayload.methodName:".setIamPolicy"'),
                    'description': 'Count of IAM policy changes.',
                    'labelExtractors': {
                        'user': (
                            'EXTRACT('
                            'protoPayload.authenticationInfo.principalEmail)'),
                    },
                    'metricDescriptor': {
                        'labels': [{
                            'description': 'Unexpected user',
                            'key': 'user',
                            'valueType': 'STRING'
                        }],
                        'unit': '1',
                        'metricKind': 'DELTA',
                        'valueType': 'INT64'
                    },
                    'metric': 'iam-policy-change-count'
                }
            },
            {
                'name': 'bucket-permission-change-count',
                'type': 'logging.v2.metric',
                'properties': {
                    'filter': (
                        '\n      resource.type=gcs_bucket AND\n      '
                        'protoPayload.serviceName=storage.googleapis.com AND\n'
                        '      '
                        '(protoPayload.methodName=storage.setIamPermissions '
                        'OR\n       '
                        'protoPayload.methodName=storage.objects.update)'),
                    'description': 'Count of GCS permissions changes.',
                    'labelExtractors': {
                        'user': (
                            'EXTRACT('
                            'protoPayload.authenticationInfo.principalEmail)'),
                    },
                    'metricDescriptor': {
                        'labels': [{
                            'description': 'Unexpected user',
                            'key': 'user',
                            'valueType': 'STRING'
                        }],
                        'unit': '1',
                        'metricKind': 'DELTA',
                        'valueType': 'INT64'
                    },
                    'metric': 'bucket-permission-change-count'
                }
            },
            {
                'name': 'bigquery-settings-change-count',
                'type': 'logging.v2.metric',
                'properties': {
                    'filter': (
                        'resource.type="bigquery_resource" AND\n'
                        'protoPayload.methodName="datasetservice.update"'),
                    'description': 'Count of bigquery permission changes.',
                    'labelExtractors': {
                        'user': (
                            'EXTRACT('
                            'protoPayload.authenticationInfo.principalEmail)'),
                    },
                    'metricDescriptor': {
                        'labels': [{
                            'description': 'Unexpected user',
                            'key': 'user',
                            'valueType': 'STRING'
                        }],
                        'unit': '1',
                        'metricKind': 'DELTA',
                        'valueType': 'INT64'
                    },
                    'metric': 'bigquery-settings-change-count'
                }
            },
            {
                'name': 'audit-configs-get-iam-etag',
                'action': ('gcp-types/cloudresourcemanager-v1:'
                           'cloudresourcemanager.projects.getIamPolicy'),
                'properties': {
                    'resource': 'my-project',
                },
                'metadata': {
                    'runtimePolicy': ['UPDATE_ALWAYS'],
                    'dependsOn': ['set-project-bindings-patch-iam-policy'],
                },
            },
            {
                'name': 'audit-configs-patch-iam-policy',
                'action': ('gcp-types/cloudresourcemanager-v1:'
                           'cloudresourcemanager.projects.setIamPolicy'),
                'properties': {
                    'updateMask': 'auditConfigs,etag',
                    'resource': 'my-project',
                    'policy': {
                        'auditConfigs': [{
                            'auditLogConfigs': [
                                {
                                    'logType': 'ADMIN_READ'
                                },
                                {
                                    'logType': 'DATA_WRITE'
                                },
                                {
                                    'logType': 'DATA_READ'
                                },
                            ],
                            'service': 'allServices',
                        }],
                        'etag': '$(ref.audit-configs-get-iam-etag.etag)',
                    },
                },
                'metadata': {
                    'dependsOn': ['audit-configs-get-iam-etag'],
                    'runtimePolicy': ['UPDATE_ON_CHANGE'],
                },
            }
        ]
    }

    self.assertEqual(generated, expected)


if __name__ == '__main__':
  absltest.main()
