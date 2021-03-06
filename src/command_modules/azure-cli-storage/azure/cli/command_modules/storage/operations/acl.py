# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def create_acl_policy(cmd, client, container_name, policy_name, start=None, expiry=None, permission=None, **kwargs):
    """Create a stored access policy on the containing object"""
    t_access_policy = cmd.get_models('common.models#AccessPolicy') or cmd.get_models('models#AccessPolicy')

    acl = _get_acl(cmd, client, container_name, **kwargs)
    acl[policy_name] = t_access_policy(permission, expiry, start)
    if hasattr(acl, 'public_access'):
        kwargs['public_access'] = getattr(acl, 'public_access')

    return _set_acl(cmd, client, container_name, acl, **kwargs)


def get_acl_policy(cmd, client, container_name, policy_name, **kwargs):
    """Show a stored access policy on a containing object"""
    acl = _get_acl(cmd, client, container_name, **kwargs)
    return acl.get(policy_name)


def list_acl_policies(cmd, client, container_name, **kwargs):
    """List stored access policies on a containing object"""
    return _get_acl(cmd, client, container_name, **kwargs)


def set_acl_policy(cmd, client, container_name, policy_name, start=None, expiry=None, permission=None, **kwargs):
    """Set a stored access policy on a containing object"""
    if not (start or expiry or permission):
        raise CLIError('Must specify at least one property when updating an access policy.')

    acl = _get_acl(cmd, client, container_name, **kwargs)
    try:
        policy = acl[policy_name]
        policy.start = start or policy.start
        policy.expiry = expiry or policy.expiry
        policy.permission = permission or policy.permission
        if hasattr(acl, 'public_access'):
            kwargs['public_access'] = getattr(acl, 'public_access')

    except KeyError:
        raise CLIError('ACL does not contain {}'.format(policy_name))
    return _set_acl(cmd, client, container_name, acl, **kwargs)


def delete_acl_policy(cmd, client, container_name, policy_name, **kwargs):
    """ Delete a stored access policy on a containing object """
    acl = _get_acl(cmd, client, container_name, **kwargs)
    del acl[policy_name]
    if hasattr(acl, 'public_access'):
        kwargs['public_access'] = getattr(acl, 'public_access')

    return _set_acl(cmd, client, container_name, acl, **kwargs)


def _get_service_container_type(cmd, client):
    from ..sdkutil import get_table_data_type
    t_block_blob_svc, t_file_svc, t_queue_svc = cmd.get_models('blob#BlockBlobService',
                                                               'file#FileService',
                                                               'queue#QueueService')
    t_table_svc = get_table_data_type(cmd.cli_ctx, 'table', 'TableService')

    if isinstance(client, t_block_blob_svc):
        return 'container'
    elif isinstance(client, t_file_svc):
        return 'share'
    elif isinstance(client, t_table_svc):
        return 'table'
    elif isinstance(client, t_queue_svc):
        return 'queue'
    else:
        raise ValueError('Unsupported service {}'.format(type(client)))


def _get_acl(cmd, client, container_name, **kwargs):
    container = _get_service_container_type(cmd, client)
    get_acl_fn = getattr(client, 'get_{}_acl'.format(container))
    lease_id = kwargs.get('lease_id', None)
    return get_acl_fn(container_name, lease_id=lease_id) if lease_id else get_acl_fn(container_name)


def _set_acl(cmd, client, container_name, acl, **kwargs):
    try:
        method_name = 'set_{}_acl'.format(_get_service_container_type(cmd, client))
        method = getattr(client, method_name)
        return method(container_name, acl, **kwargs)
    except TypeError:
        raise CLIError("Failed to invoke SDK method {}. The installed azure SDK may not be"
                       "compatible to this version of Azure CLI.".format(method_name))
    except AttributeError:
        raise CLIError("Failed to get function {} from {}. The installed azure SDK may not be "
                       "compatible to this version of Azure CLI.".format(client.__class__.__name__, method_name))
