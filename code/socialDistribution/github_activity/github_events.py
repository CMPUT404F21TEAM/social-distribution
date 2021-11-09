from datetime import datetime, timezone
import timeago

class GithubEvent:
    ''' Github Event parent class, must be subclassed
    '''

    def __init__(self, event_data=None):
        ''' Constructor, receives optional event_data object of type dictionary
        '''
        if event_data is not None:
            self.set_event_data(event_data)

    def set_event_data(self, event_data):
        ''' Extract event information from event_data object of type dictionary
        '''
        self.payload = event_data["payload"]
        self.actor = event_data["actor"]["login"]
        self.repo = event_data["repo"]
        self.repo_name = self.repo["name"].split("/")[-1]   # get repo name only
        self.action = self.payload.get("action")            # defaults to None
        self.created_at = event_data["created_at"]

    def time_ago(self):
        ''' Get when the event in question was created
        '''
        now = datetime.now(timezone.utc)
        dt_created_at = datetime.strptime(
            self.created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return timeago.format(dt_created_at, now)

    def get_description(self):
        ''' Must be implemented by sub-class
        '''
        raise NotImplementedError("Failed to implement get_description")

class CreateEvent(GithubEvent):

    def get_description(self):
        ref_type = self.payload["ref_type"]
        if ref_type == "repository":
            return f"{self.actor} created a new {ref_type} called {self.repo_name}"

        else:
            return f"{self.actor} created a new {ref_type} in {self.repo_name}"


class DeleteEvent(GithubEvent):

    def get_description(self):
        ref_type = self.payload["ref_type"]
        if ref_type == "repository":
            return f"{self.actor} deleted a {ref_type} called {self.repo_name}"

        else:
            return f"{self.actor} deleted a {ref_type} in {self.repo_name}"


class CommitCommentEvent(GithubEvent):

    def get_description(self):
        comment = self.payload["body"]
        return f"{self.actor} commented, \'{comment}\', on {self.repo_name}"


class PushEvent(GithubEvent):

    def get_description(self):
        remote_branch = self.payload["ref"].split("/", 2)[-1]   # remove refs/head/ part
        num_commits = self.payload["distinct_size"]

        if num_commits == 1:
            return f"{self.actor} pushed {num_commits} commit to {remote_branch} in {self.repo_name}"
        else:
            return f"{self.actor} pushed {num_commits} commits to {remote_branch} in {self.repo_name}"


class ForkEvent(GithubEvent):

    def get_description(self):
        forkee_obj = self.payload["forkee"]
        repo_html_url = forkee_obj["html_url"]
        repo_owner = self.repo["name"].split("/")[0]

        return f"{self.actor} forked the repository, {self.repo_name}, from {repo_owner}: {repo_html_url}"


class GollumEvent(GithubEvent):

    def get_description(self):
        page = self.payload["pages"][0]
        page_action = page["action"]
        page_name = page["page_name"]
        return f"{self.actor} {page_action} the \'{page_name}\' wiki page"

class IssuesEvent(GithubEvent):

    def get_description(self):
        issue_num = self.payload["issue"]["number"]
        issue_title = self.payload["issue"]["title"]
        descr = ""

        if self.action == "labelled":
            label_name = self.payload["label"]["name"]
            descr = f"{self.actor} added the label, \'{label_name}\' to"

        elif self.action == "unlabelled":
            label_name = self.payload["label"]["name"]
            descr = f"{self.actor} removed the label, \'{label_name}\' from"

        else:
            descr = f"{self.actor} {self.action}"

        descr += f" issue #{issue_num}, \'{issue_title}\', in {self.repo_name}"
        return descr


class MemberEvent(GithubEvent):

    def get_description(self):
        if self.action == "edited":
            return f"{self.actor} {self.action} collaborator permissions for {self.repo_name}"

        else:
            member = self.payload["member"]["login"]
            return f"{self.actor} {self.action} {member} as a collaborator on {self.repo_name}"


class PublicEvent(GithubEvent):

    def get_description(self):
        return f"{self.actor} made the following repository public: {self.repo_name}"


class PullRequestEvent(GithubEvent):

    def get_description(self):
        pull_request = self.payload["pull_request"]
        pr_title = pull_request["title"]
        descr = ""

        if self.action in ["assigned", "unassigned"]:
            assignee = pull_request["assignee"]["login"]
            descr = f"{self.actor} {self.action} {assignee} in the pull request, \'{pr_title}\',"

        elif self.action in ["review_requested", "review_request_removed"]:
            requested_reviewers = [reviewer_obj["login"]
                for reviewer_obj in pull_request["requested_reviewers"]]

            if self.action == "review_requested":
                descr = f"{self.actor} requested review from "
                for reviewer in requested_reviewers:
                    descr += f"{reviewer},"

            else:
                descr = f"{self.actor} removed request for review"

            descr += f" on the pull request, \'{pr_title}\',"

        elif self.action == "labelled":
            descr = f"{self.actor} added a label to the pull request, \'{pr_title}\',"

        elif self.action == "unlabelled":
            descr = f"{self.actor} removed a label from the pull request, \'{pr_title}\',"

        elif self.action == "synchronize":
            descr = f"{self.actor} synchronized the pull request, \'{pr_title}\', with its source branch"
        
        else:
            descr = f"{self.actor} {self.action} a pull request, \'{pr_title}\',"

        descr += f" for {self.repo_name}"
        return descr


class PullRequestReviewEvent(GithubEvent):

    def get_description(self):
        pull_request = self.payload["pull_request"]
        pr_title = pull_request["title"]

        return f"{self.actor} {self.action} a pull request review for \'{pr_title}\' in {self.repo_name}"


class PullRequestReviewCommentEvent(GithubEvent):

    def get_description(self):
        comment_obj = self.payload["comment"]
        comment = comment_obj["body"]
        pull_request = self.payload["pull_request"]
        pr_title = pull_request["title"]

        return f"{self.actor} commented \'{comment}\' on the pull request, \'{pr_title}\', in {self.repo_name}"


class ReleaseEvent(GithubEvent):

    def get_description(self):
        return f"{self.actor} {self.action} a release for {self.repo_name}"


class WatchEvent(GithubEvent):

    def get_description(self):
        return f"{self.actor} starred {self.repo_name}"


class EventFactory:

    def get_event(self, event_name):
        if event_name == 'PushEvent':
            return PushEvent()

        elif event_name == "CommitCommentEvent":
            return CommitCommentEvent()

        elif event_name == "CreateEvent":
            return CreateEvent()

        elif event_name == "DeleteEvent":
            return DeleteEvent()

        elif event_name == "ForkEvent":
            return ForkEvent()

        elif event_name == "PublicEvent":
            return PublicEvent()

        elif event_name == "MemberEvent":
            return MemberEvent()

        elif event_name == "PullRequestEvent":
            return PullRequestEvent()

        elif event_name == "PullRequestReviewEvent":
            return PullRequestReviewEvent()

        elif event_name == "PullRequestReviewCommentEvent":
            return PullRequestReviewCommentEvent()

        elif event_name in ["IssuesEvent", "IssueCommentEvent"]:
            return IssuesEvent()

        elif event_name == "WatchEvent":
            return WatchEvent()

        elif event_name == "ReleaseEvent":
            return ReleaseEvent()
        
        else:
            raise Exception("Unsupported event type")