#!/usr/bin/env python
#
#   Two Factor Auth (TOTP) Command line interface
#
#

import os
import sys
import argparse

from django.core.management import base

# import horizon totp plugin libraries
from openstack_dashboard.auth.totp_oracle import TOTPOracle
from openstack_dashboard.auth.exception import IllegalArgument

# check current environment for specific keys
def env(*vars, **kwargs):
    for v in vars:
        value = os.environ.get(v)
        if value:
            return value

    return kwargs.get('default', '')


class Command(base.BaseCommand):
    def __init__(self, parser_class=argparse.ArgumentParser):
        super(Command, self).__init__()
        self.parser_class = parser_class

    def conn_values_check(self, options):
        if not options.get('os_username'):
            raise ValueError('os-username must to be set')
        if not options.get('os_auth_url'):
            raise ValueError('os-auth-url must to be set')
        if not options.get('os_password'):
            raise ValueError('os-password must to be set')
        if not options.get('project_name'):
            raise ValueError('project_name must to be set')
        if not options.get('project_domain_name'):
            raise ValueError('project_domain_name must to be set')
        if not options.get('user_domain_name'):
            raise ValueError('user_domain_name must to be set')

        return True

    def disable(self, options):
        os_password = options.get('os_password')
        os_auth_url = options.get('os_auth_url')
        os_username = options.get('os_username')
        project_name = options.get('project_name')
        project_domain_name = options.get('project_domain_name')
        user_domain_name = options.get('user_domain_name')
        if not (os_auth_url and os_password and os_username):
            raise IllegalArgument("Username, password and auth url are required")

        user_id = options.get('user_id')
        if not (os_auth_url and os_password and os_username):
            raise IllegalArgument("User id is required")

        token_oracle = TOTPOracle(auth_url=os_auth_url, username=os_username, password=os_password, project_name=project_name, project_domain_name=project_domain_name, user_domain_name=user_domain_name)
        token_oracle.disable(user_id)

    def add_arguments(self, parser):
        parser.add_argument('--os-username',
                            metavar='<auth-user-name>',
                            default=env('OS_USERNAME'),
                            help='Name used for authentication with the '
                                 'OpenStack Identity service. '
                                 'Defaults to env[OS_USERNAME].')

        parser.add_argument('--os-password',
                            metavar='<auth-password>',
                            default=env('OS_PASSWORD'),
                            help='Password used for authentication with the '
                                 'OpenStack Identity service. '
                                 'Defaults to env[OS_PASSWORD].')

        parser.add_argument('--os-auth-url',
                            metavar='<auth-url>',
                            default=env('OS_AUTH_URL'),
                            help='Specify the Identity endpoint to use for '
                                 'authentication. '
                                 'Defaults to env[OS_AUTH_URL].')

        parser.add_argument('--project-name',
                            metavar='<project_name>',
                            default=env('OS_PROJECT_NAME'),
                            help='Admin project name'
                                 'Defaults to env[OS_PROJECT_NAME].')
                            
        parser.add_argument('--project-domain-name',
                            metavar='<project_domain_name>',
                            default=env('OS_PROJECT_DOMAIN_NAME'),
                            help='Admin project domain name'
                                 'Defaults to env[OS_PROJECT_DOMAIN_NAME].')

        parser.add_argument('--user-domain-name',
                            metavar='<user_domain_name>',
                            default=env('OS_USER_DOMAIN_NAME'),
                            help='Admin user domain name'
                                 'Defaults to env[OS_USER_DOMAIN_NAME].')

        parser.add_argument('--user-id',
                            metavar='<user_id>',
                            default=None,
                            help='Specify the user id for which TOTP must be disabled')

    def handle(self, *args, **options):
        self.conn_values_check(options)
        if options.get('user_id') is not None:
            self.disable(options)
        else:
            print("syntax error: user-id is missing")


