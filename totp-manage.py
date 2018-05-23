#!/usr/bin/env python
#
#   Two Factor Auth (TOTP) Command line interface
#
#

import os
import sys
import argparse

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


class TwoFactorCliShell(object):
    def __init__(self, parser_class=argparse.ArgumentParser):
        self.parser_class = parser_class

    def conn_values_check(self, options):
        if not options.os_username:
            raise ValueError('os-username must to be set')
        if not options.os_auth_url_v3:
            raise ValueError('os-auth-url-v3 must to be set')
        if not options.os_password:
            raise ValueError('os-password must to be set')

        return True

    def disable(self, options):
        os_password = options.os_password
        os_auth_url_v3 = options.os_auth_url_v3
        os_username = options.os_username
        if not (os_auth_url_v3 and os_password and os_username):
            raise IllegalArgument("Username, password and auth url are required")

        user_id = options.user_id
        if not (os_auth_url_v3 and os_password and os_username):
            raise IllegalArgument("User id is required")

        token_oracle = TOTPOracle(auth_url=os_auth_url_v3, username=os_username, password=os_password)
        token_oracle.disable(user_id)

    def get_base_parser(self):
        parser = self.parser_class(prog='totp-cli', description="TOTP Command Line Interface")

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

        parser.add_argument('--os-auth-url-v3',
                            metavar='<auth-url>',
                            default=env('OS_AUTH_URL_V3'),
                            help='Specify the Identity endpoint to use for '
                                 'authentication. '
                                 'Defaults to env[OS_AUTH_URL_V3].')

        return parser

    def get_sub_parser(self, parser):
        subparsers = parser.add_subparsers(help='<sub-command> -h for help')

        subparser_disable = subparsers.add_parser('disable', help='disable -h')
        subparser_disable.add_argument('--user-id', help='user id', required=True)
        subparser_disable.set_defaults(func=self.disable)

        return parser

    def main(self, argv):
        parser = self.get_base_parser()
        parser = self.get_sub_parser(parser)

        options = parser.parse_args(argv)

        self.conn_values_check(options)

        options.func(options)

        parser.parse_args(argv)

        if not argv:
            parser.print_help()
        return 0


def main():
    try:
        TwoFactorCliShell().main(sys.argv[1:])

    except Exception as e:
        print('Error: ' + repr(e))
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
