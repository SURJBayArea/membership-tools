#!/usr/bin/env python3
import csv
import logging
import os
import fire

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Member(object):
    def __init__(self, name, email, committee=None, active=False):
        self.name = name
        self.email = email
        self.committee = committee
        self.active = active

    def gmail_norm(email):
        [name, domain] = email.split('@')
        name_norm = name.replace('.', '')
        return "%s@%s" % (name_norm, domain)


    def __eq__(self, other):
        if not isinstance(other, Member):
            return false

        if self.email.lower() == other.email.lower():
            return True
        else:
            if self.name.lower() == other.name.lower():
                LOG.warn("matched %s by name - %s / %s" % (self.name, self.email, other.email))
                return True
            elif len(self.name) > 0 and len(other.name) > 0 and \
                 self.name.lower().find(other.name.lower()) > -1:
                LOG.warn("fuzzy matched %s by name - %s / %s" % (self.name, self.email, other.email))
                return True
            elif Member.gmail_norm(self.email) == Member.gmail_norm(other.email):
                LOG.warn("fuzzy matched %s by gmail-normalized email %s / %s" % (self.name, self.email, other.email))
                return True
            else:
                return False

    def contains(other, others):
        for member in others:
            if other == member:
                return True

        return False

    def __str__(self):
        return "%s <%s>" % (self.name, self.email)

    def __repr__(self):
        return self.__str__()
    
class CompareLists(object):
    def _an_reader(self, an_export):
        if not os.path.exists(an_export):
            raise Exception("unable to find action network export %s" % an_export)
        an_members = []
        with open(an_export, 'r') as an_csv:
            for an_row in csv.reader(an_csv):
                if an_row[0].startswith('#'):
                    continue
                if an_row[0] == 'first_name':
                    continue
                if len(an_row) == 3:
                    [first_name, last_name, email] = an_row
                    an_members.append(Member("%s %s" % (first_name, last_name), email, active=True))
                elif len(an_row) >= 4:
                    first_name = an_row[0]
                    last_name = an_row[1]
                    email = an_row[2]
                    committee = an_row[3]
                    an_members.append(Member("%s %s" % (first_name.strip(), last_name.strip()), email, committee, active=True))
                else:
                    raise Exception("unexpected action network report format")
        return an_members

    def _group_reader(self, group_export):
        if not os.path.exists(group_export):
            raise Exception("unable to find google group membership export %s" % group_export)

        group_members = []
        with open(group_export, 'r') as g_csv:
            for g_row in csv.reader(g_csv):
                if g_row[0].startswith('#'):
                    continue
                if g_row[0].startswith('Members for group') or \
                   g_row[0] == 'Email address':
                    continue
                email = g_row[0]
                name = g_row[1]
                group_members.append(Member(name, email, active=True))
        return group_members

    def _slack_reader(self, slack_export):
        if not os.path.exists(slack_export):
            raise Exception("unable to find slack export %s" % slack_export)

        slack_members = []
        with open(slack_export, 'r') as s_csv:
            for s_row in csv.reader(s_csv):
                if s_row[0].startswith('#'):
                    continue
                if s_row[0] == 'username':
                    continue

                email = s_row[1]
                name = s_row[7]
                active = False
                if s_row[2] == 'Member' or s_row[2] == 'Admin' or s_row[2] == 'Owner':
                    active = True
                
                slack_members.append(Member(name, email, active=active))

        return slack_members


    def audit_group(self, an_export, group_export):

        an_members = self._an_reader(an_export)
        group_members = self._group_reader(group_export)
        LOG.info("read %s an members, %s google group members" % (len(an_members), len(group_members)))

        missing_count = 0
        for group_member in group_members:
            email_bits = group_member.email.split('@')
            if email_bits[1] == 'surjbayarea.org':
                LOG.warn("ignoring likely group membership email %s" % group_member.email)
                continue

            if email_bits[0].lower().find('surj') >= 0:
                LOG.warn("ignoring possible group alias email %s" % group_member.email)
                continue

            if not Member.contains(group_member, an_members):
                print("%s not found in action network" % (group_member))
                missing_count += 1

        print("%s out of %s group members are missing from action network" % (missing_count, len(group_members)))

    def audit_slack(self, an_export, slack_export):
        slack_members = self._slack_reader(slack_export)
        an_members = self._an_reader(an_export)
        LOG.info("read %s an members, %s slack members" % (len(an_members), len(slack_members)))

        missing_count = 0
        inactive_count = 0
        for slack_member in slack_members:
            if not slack_member.active:
                inactive_count += 1
                continue

            if not Member.contains(slack_member, an_members):
                print("%s not found in action network" % (slack_member))
                missing_count += 1

        print("%s out of %s active slack members are missing from action network" % (missing_count, len(slack_members) - inactive_count))


    def missing_slack(self, an_export, slack_export):
        an_members = self._an_reader(an_export)
        slack_members = [x for x in self._slack_reader(slack_export) if x.active]
        LOG.info("read %s an members, %s slack members" % (len(an_members), len(slack_members)))
        missing_members = []
        for an_member in an_members:
            if not Member.contains(an_member, slack_members):
                missing_members.append(an_member)

        print(','.join([str(x) for x in missing_members]))

    def missing_group(self, an_export, group_export, csv_list=False, committee=None):
        an_members = self._an_reader(an_export)
        group_members = self._group_reader(group_export)
        LOG.info("read %s an members, %s google group members" % (len(an_members), len(group_members)))
        missing_members = []
        for an_member in an_members:
            if not Member.contains(an_member, group_members):
                missing_members.append(an_member)

        committee_members = {}
        for member in missing_members:
            if member.committee not in committee_members:
                committee_members[member.committee] = [member]
            else:
                committee_members[member.committee].append(member)

        if committee not in committee_members:
            raise Exception("%s committee not found" % committee)

        if csv_list:
            if committee:
                print(','.join([str(x) for x in committee_members[committee]]))
            else:
                print(','.join([str(x) for x in missing_members]))
        else:
            for iter_committee in committee_members.keys():
                if committee and committee != iter_committee:
                    continue
                print("\n# Committee - %s\n" % iter_committee)
                for member in committee_members[iter_committee]:
                    print("  %s" % member)

if __name__ == '__main__':
    fire.Fire(CompareLists)
