from django.conf import settings
from jira import JIRA, JIRAError
from string import Template
import re


class JiraSender(object):
    tpl = Template('\n'.join(
        [
            '*Current State*: $state',
            '*Host*: $host_name',
            '*Service*: $service_name',
            '*Output*: $output',
        ]
    ))

    def __init__(self):
        self.rest_api_user = settings.JIRA_USER_NAME
        self.rest_api_password = settings.JIRA_USER_PASSWORD
        self.rest_api_url = settings.JIRA_ENDPOINT

        self.jira = JIRA(basic_auth=(self.rest_api_user, self.rest_api_password),
                         options={'server': self.rest_api_url},
                         timeout=30)

    def __get_param(self, data: dict, name: str, default_value=None):
        val = data.get(name)
        if val is None:
            val = default_value
        return val

    def create_ticket(self, project: str, data: dict):
        host_name = self.__get_param(data, 'host_name')
        service_name = self.__get_param(data, 'service_name')
        status = self.__get_param(data, 'status')
        service_state = status.name if status is not None else 'FAIL'
        output = self.__get_param(data, 'output', '')
        assignee = self.__get_param(data, 'assignee', [])
        watchers = self.__get_param(data, 'watchers', [])
        tags = self.__get_param(data, 'tags', [])

        priority = self.__get_param(data, 'priority', settings.JIRA_PRIORITY)
        issue_type = self.__get_param(data, 'issue_type', settings.JIRA_ISSUE_TYPE)
        transition_resolved_id = self.__get_param(data, 'transition_resolved_id',
                                                  settings.JIRA_TRANSITION_RESOLVED_ID)
        close_when_restore = self.__get_param(data, 'close_when_restore', settings.JIRA_CLOSE_WHEN_RESTORE)
        post_comments = self.__get_param(data, 'post_comments', settings.JIRA_POST_COMMENTS)
        triggering_status = self.__get_param(data, 'triggering_status', settings.JIRA_TRIGGERING_STATUS)

        try:
            if isinstance(watchers, str):
                watchers_list = re.findall(r'[^,\s]+', watchers)
            elif isinstance(watchers, list):
                watchers_list = watchers
            else:
                watchers_list = []

            if isinstance(tags, str):
                labels = re.findall(r'[^,\s]+', tags)
            elif isinstance(tags, list):
                labels = tags
            else:
                labels = []
            labels.append('nogios')

            subject = 'NOGIOS: {} {}'.format(host_name, service_name)
            search_filter = 'summary ~ "{}" AND status not in (Resolved, Closed, Done) AND project="{}"'\
                .format(subject, project)

            existing_issues = self.jira.search_issues(search_filter)

            issue_dict = {
                'project': project,
                'summary': subject,
                'description': self.tpl.substitute({
                    'host_name': host_name, 'service_name': service_name,
                    'state': service_state, 'output': output,
                }),
                'issuetype': {'name': issue_type},
                'priority': {'name': priority}
            }

            if existing_issues is None or len(existing_issues) == 0:
                if service_state == triggering_status or service_state == settings.JIRA_TRIGGERING_STATUS:
                    new_issue = self.jira.create_issue(fields=issue_dict)
                    try:
                        new_issue.update(fields={"labels": labels})
                    except JIRAError as e:
                        print("Error: unable to add labels to a Jira ticket:", str(e))
                    for watcher in watchers_list:
                        try:
                            self.jira.add_watcher(new_issue.id, watcher)
                        except JIRAError as e:
                            print("Error: unable to add watchers to a Jira ticket:", str(e))

                    self.__add_comments(post_comments, new_issue.key, issue_dict['description'])
                    if re.match(r'^[\S]+\@[\S]+$', assignee) is not None:
                        self.jira.assign_issue(new_issue, assignee)
            else:
                current_issue = existing_issues[0]
                if service_state == settings.JIRA_TYPE_OK and current_issue.fields.assignee is None:
                    self.__add_comments(post_comments, current_issue.key, issue_dict['description'])
                    if close_when_restore:
                        self.jira.transition_issue(current_issue.key,
                                                   transition=transition_resolved_id,
                                                   # resolution={'id': RESOLUTION_ID}
                                                   )
                else:
                    self.__add_comments(post_comments, current_issue.key, issue_dict['description'])
        except Exception as ex:
            print("ERROR: unable to create Jira ticket:", ex)

    def __add_comments(self, post_comments, issue_key: str, comment_text: str):
        if post_comments:
            self.jira.add_comment(issue_key, comment_text)
