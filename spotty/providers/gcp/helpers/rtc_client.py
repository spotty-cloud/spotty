import googleapiclient.discovery


class RtcClient(object):

    def __init__(self, project_id: str, zone: str):
        self._project_id = project_id
        self._zone = zone
        self._rtc = googleapiclient.discovery.build('runtimeconfig', 'v1beta1', cache_discovery=False)

    def get_value(self, config_name, template):
        config_name = 'projects/%s/configs/%s' % (self._project_id, config_name)
        fields = ['/failure']
        res = self._rtc.projects().get(name=config_name, fields=fields).execute()

        return res
