from ..utilities.date_utilities import format_datetime_string
from .processing_config import basketball_rename_fields as rename_fields
from .processing_config import basketball_date_fields as date_fields
from .processing_config import basketball_integer_fields as integer_fields

class NBADataInstance():
    def __init__(self, tableClass, data, event_id=None, **kwargs):
        self.tableClass=tableClass
        self.table_name=tableClass.__table__.name
        self.create()
        if data:
            data=self.rename_data_fields(data)
            data=self.reformat_date_fields(data)
            data=self.reformat_integer_fields(data)
            self.fill(data, event_id)
        self.update(**kwargs)

    def rename_data_fields(self, data):
        if self.table_name in rename_fields:
            for key, value in rename_fields[self.table_name].items():
                if key in data:
                    new_key=rename_fields[self.table_name][key]
                    data[new_key]=data.pop(key)
        return data

    def reformat_date_fields(self, data):
        if self.table_name in date_fields:
            for key in date_fields[self.table_name]:
                if key in data:
                    date_string=data[key]
                    if date_string is not None:
                        data[key] = format_datetime_string(date_string)
        return data

    def reformat_integer_fields(self, data):
        if self.table_name in integer_fields:
            for key in integer_fields[self.table_name]:
                if key in data:
                    try:
                        data[key]=int(data[key])
                    except:
                        pass
        return data

    def create(self):
        self.instance={}
        for col in self.tableClass.__table__.c:
            if not col.primary_key:
                if col.default is not None:
                    self.instance.update({col.name: col.default.arg})
                else:
                    self.instance.update({col.name: None})

    def fill(self, data, event_id):
        for key, value in data.items():
            if value is not None:
                if key in self.instance:
                     self.instance[key]=value
        if event_id:
            self.fill_event_id_data(event_id)
        self.fill_fg2_data()
        self.fill_sec_data()
        self.strip_text()

    def fill_event_id_data(self, event_id):
        if 'event_id' in self.instance:
            self.instance['event_id'] = event_id

    def fill_fg2_data(self):
        if (('fg2a' in self.instance)
            and ('fg3a' in self.instance)
            and ('fga' in self.instance)):
            self.instance['fg2a']=(self.instance['fga'] - self.instance['fg3a'])
        if (('fg2m' in self.instance)
            and ('fg3m' in self.instance)
            and ('fgm' in self.instance)):
            self.instance['fg2m']=(self.instance['fgm'] - self.instance['fg3m'])

    def fill_sec_data(self):
        if 'min' in self.instance:
            if self.instance['min'] is not None:
                try:
                    min, sec=self.instance['min'].split(':')
                    self.instance['sec']=int(min) * 60 + int(sec)
                except AttributeError:
                    if self.instance['min']==0:
                        self.instance['sec']=0

    def strip_text(self):
        for key, value in self.instance.items():
            try:
                self.instance[key] = value.strip()
            except AttributeError:
                pass

    def update(self, **kwargs):
        if 'home_team_id' in kwargs:
            if self.instance['team_id'] == kwargs.get('home_team_id'):
                self.instance['home_away'] = True
            else:
                self.instance['home_away'] = False
        if 'game_date' in kwargs:
            if self.instance['game_date_est'] is None:
                self.instance['game_date_est'] = kwargs.get('home_team_id')
        for key, value in kwargs.items():
            if key in self.instance:
                self.instance[key]=value
