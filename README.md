# SURJ Bay Area Membership Tools

These require Python3 and shoudl get wrapped in a docker container for ease of use. In the meantime, there is [virtualenv](https://virtualenv.pypa.io/en/latest/)

## `compare_lists.py`

This script is used to quickly compare exports of various member lists. It can compare Slack and Google Groups against the Action Network report provided. When generating the Action Network report two formats are supported. The script will attempt to compare emails however it no matching email is found it will attempt to compare against the full name, however will throw a warning with both emails in this case.

* `first_name,last_name,email`
* `first_name,last_name,email,committee`

The script may be invoked in three ways.

To check Google Groups membership. This will return a list of emails and names.

```
$ ./compare-lists.py audit_group action-network-report.csv google-group-members.csv
```

To check Slack membership. This will return a list of emails and names.

```
$ ./compare-lists.py audit_slack action-network-report.csv slack-members.csv
```

To check to see who is missing from a Google Group. This will return a CSV list of properly formatted email + name which may be used to invite people to a Google Group.

```
$ ./compare-lists.py missing_group action-network-report.csv google-group-members.csv
```
