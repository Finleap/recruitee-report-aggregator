import logging
from functools import reduce
from os import getenv

import pandas as pd
import requests
from dotenv import load_dotenv

# https://api.recruitee.com/c/123/stats/candidates

BASE_URL = "https://api.recruitee.com"
logging.basicConfig(level=logging.DEBUG)


class Recruitee:
    AUTH_KEY = None

    def __init__(self, name, company_id):
        self.url = "/".join([BASE_URL, "c", company_id])
        self.auth_param = {"auth_token": Recruitee.AUTH_KEY}
        self.name = name

    def get(self, resource, params=None):
        """
        params:
        date_range
        Date filter. Can be: range, today, yesterday, this_week, last_week, this_month,
        last_month, this_quarter, last_quarter, this_year, last_year, last_30_days,
        last_60_days. If value is range, additional parameters ‘date_start’ and ‘date_end’ must be provideda

        """
        if params is None:
            params = {}
        get_params = {}
        get_params.update(self.auth_param)
        get_params.update(params)
        response = requests.get("/".join([self.url, resource]), params=self.auth_param)
        logging.info(response.url)
        return response.json()

    @staticmethod
    def this_month():
        return {'date_range': "this_month"}

    @staticmethod
    def last_month():
        return {'date_range': "last_month"}

    @staticmethod
    def this_quarter():
        return {'date_range': "this_quarter"}

    @staticmethod
    def last_quarter():
        return {'date_range': "last_quarter"}

    def generic_parser(self, response, name_index=None, target_columns=None):
        provided_columns = response['columns']

        data = []
        indexes = []
        for values in response['values']:
            job_name = values[name_index]
            if not job_name or job_name in ['Testjob']:
                continue
            indexes.append(Recruitee.clean(job_name))
            d = {}
            for column in target_columns:
                index = provided_columns.index(column)
                value = values[index]

                d[column] = value
            data.append(d)

        # multiindexing with company name
        return pd.DataFrame(data, columns=target_columns, index=[indexes, [self.name] * indexes.__len__()])

    def quality_of_candidates(self, params):
        qoc = self.get('/report/candidates/quality_of_candidates', params)
        df = self.generic_parser(qoc, 0,
                                 ["total_count", "moved_forward_count",
                                  "disqualified_count", "interviewed_count",
                                  "offered_count", "hired_count"])
        return df

    def pipeline_speed(self, params):
        ps = self.get('/report/candidates/pipeline_speed', params)
        df = self.generic_parser(ps, 0,
                                 ["total_count", "applied_count", "sourced_count", "phone_screened_count",
                                  "interviewed_count", "evaluated_count", "offered_count"])
        return df

    def proceed_rate(self, params):
        ps = self.get('/report/candidates/proceed_rate', params)
        df = self.generic_parser(ps, 0,
                                 ["total_count", "applied_count", "sourced_count", "phone_screened_count",
                                  "interviewed_count", "evaluated_count", "offered_count"])
        return df

    def time_to_hire(self, params):
        tth = self.get('/report/candidates/time_to_hire', params)
        df = self.generic_parser(tth, 0,
                                 ["total_count", "hired_count", "min_minutes", "max_minutes", "avg_minutes"])
        return df

    @staticmethod
    def clean(name):
        removables = ['(m/f/div)', '(f/m/div)', '(w/m/div)', '(m/f)', '(m/w)']
        for r in removables:
            if name.find(r) > 0:
                return name.replace(r, '')
        return name


def get_recruitee(company_name):
    company_id = getenv(company_name)
    if company_id:
        return Recruitee(company_name, company_id)
    else:
        raise ('make sure .env file contains company name ', company_name)


if __name__ == "__main__":
    load_dotenv()
    Recruitee.AUTH_KEY = getenv("AUTH_TOKEN")

    clients = [get_recruitee('perseus'), get_recruitee('infinitec'), get_recruitee('dfs')]

    qoc_result = reduce((lambda x, y: x.append(y)), map(lambda x: x.quality_of_candidates(Recruitee.last_quarter()), clients))
    ps_result = reduce((lambda x, y: x.append(y)), map(lambda x: x.proceed_rate(Recruitee.last_quarter()), clients))
    pr_result = reduce((lambda x, y: x.append(y)), map(lambda x: x.pipeline_speed(Recruitee.last_quarter()), clients))
    tth_result = reduce((lambda x, y: x.append(y)), map(lambda x: x.time_to_hire(Recruitee.last_quarter()), clients))

    with pd.ExcelWriter('output.xlsx') as writer:  # doctest: +SKIP
        qoc_result.to_excel(writer, sheet_name='quality of candidates')
        ps_result.to_excel(writer, sheet_name='pipeline speed')
        pr_result.to_excel(writer, sheet_name='proceed rate')
        tth_result.to_excel(writer, sheet_name='time_to_hire')
