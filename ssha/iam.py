from . import aws, errors


_cache = {}


def _list_groups_for_user(username):

    iam = aws.client('iam')

    print('[ssha] discovering iam groups')

    groups = []

    marker = None
    while True:

        kwargs = {
            'UserName': username,
        }
        if marker:
            kwargs['Marker'] = marker

        response = iam.list_groups_for_user(**kwargs)
        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            errors.json_exit(response)

        for group in response['Groups']:
            groups.append(group['GroupName'])

        marker = response.get('Marker')
        if not marker:
            return groups


def groups():
    if 'groups' not in _cache:
        username = user()
        if username:
            _cache['groups'] = _list_groups_for_user(username)
        else:
            _cache['groups'] = []
    return _cache['groups']


def user():
    if 'user' not in _cache:
        creds = aws.credentials()
        if creds.method == 'assume-role':
            _cache['user'] = None
        else:
            print('[ssha] discovering iam user')
            iam = aws.resource('iam')
            user = iam.CurrentUser()
            _cache['user'] = user.user_name
    return _cache['user']
