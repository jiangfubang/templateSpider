# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name:       utils
   Description :
   Author:          jiangfb
   date:            2021-02-25
-------------------------------------------------
   Change Activity:
                    2021-02-25:
-------------------------------------------------
"""
import logging
from datetime import datetime, timedelta

from $project_name.common.dbutil import DataBase

__author__ = 'jiangfb'

logger = logging.getLogger(__name__)

def get_user_keywords():
    logger.info("获取搜索账户关键字")
    sql = "SELECT keyword FROM tb_keyword WHERE type=3 and content_type=1 and keyword_status=0;"
    keywords = DataBase().queryall(sql)
    logger.info("搜索账户关键字：" + "|".join(keywords))
    return keywords


def get_delta_datetime(days) -> datetime:
    if days == -1:
        return datetime.strptime("1970-01-01 00:00:00", '%Y-%m-%d %H:%M:%S')
    now = datetime.now()
    delta = timedelta(days=days)
    n_days_forward = now - delta
    return n_days_forward

if __name__ == '__main__':
    print(get_delta_datetime(168))

def get_accounts(deal_type='all', content_type='minivideo'):
    logger.info(f"获取 [{content_type}] [{deal_type}] 账户")
    if deal_type == 'add' and content_type == 'minivideo':
        sql = """SELECT user_id,scrapy_hours,scrapy_nums FROM tb_source_user WHERE source_channel='渠道' AND dept_name='2' AND user_status = 0 AND status_3=0 AND create_time < DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d') AND scrapy_days = 0 AND user_id!='-';"""
    elif deal_type == 'all' and content_type == 'minivideo':
        sql = """SELECT user_id,scrapy_days,scrapy_nums FROM
                (
                SELECT user_id,scrapy_days,scrapy_nums FROM tb_source_user WHERE source_channel='渠道' AND dept_name='2' AND user_status = 0 AND status_3=0 AND create_time = DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d') AND user_id!='-'
                UNION ALL
                SELECT user_id,scrapy_days,scrapy_nums FROM tb_source_user WHERE source_channel='渠道' AND dept_name='2' AND user_status = 0 AND status_3=0 AND create_time < DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d') AND scrapy_days > 0 AND user_id!='-'
                ) a;"""
    elif deal_type == 'add' and content_type == 'video':
        sql = """SELECT user_id,scrapy_hours,scrapy_nums FROM tb_source_user WHERE source_channel='渠道' AND dept_name='2' AND user_status = 0 AND status_2=0 AND create_time < DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d') AND scrapy_days = 0 AND user_id!='-';"""
    elif deal_type == 'all' and content_type == 'video':
        sql = """SELECT user_id,scrapy_days,scrapy_nums FROM
                (
                SELECT user_id,scrapy_days,scrapy_nums FROM tb_source_user WHERE source_channel='渠道' AND dept_name='2' AND user_status = 0 AND status_2=0 AND create_time = DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d') AND user_id!='-'
                UNION ALL
                SELECT user_id,scrapy_days,scrapy_nums FROM tb_source_user WHERE source_channel='渠道' AND dept_name='2' AND user_status = 0 AND status_2=0 AND create_time < DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d') AND scrapy_days > 0 AND user_id!='-'
                ) a;"""
    elif deal_type == 'add' and content_type == 'article':
        sql = """SELECT user_id,scrapy_hours,scrapy_nums FROM tb_source_user WHERE source_channel='渠道' AND dept_name='2' AND user_status = 0 AND status_1=0 AND create_time < DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d') AND scrapy_days = 0 AND user_id!='-';"""
    elif deal_type == 'all' and content_type == 'article':
        sql = """SELECT user_id,scrapy_days,scrapy_nums FROM
                (
                SELECT user_id,scrapy_days,scrapy_nums FROM tb_source_user WHERE source_channel='渠道' AND dept_name='2' AND user_status = 0 AND status_1=0 AND create_time = DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d') AND user_id!='-'
                UNION ALL
                SELECT user_id,scrapy_days,scrapy_nums FROM tb_source_user WHERE source_channel='渠道' AND dept_name='2' AND user_status = 0 AND status_1=0 AND create_time < DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d') AND scrapy_days > 0 AND user_id!='-'
                ) a;"""
    elif deal_type == 'add' and content_type == 'news':
        sql = """SELECT user_id,scrapy_hours,scrapy_nums FROM tb_source_user WHERE source_channel='渠道' AND dept_name='2' AND user_status = 0 AND status_4=0 AND create_time < DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d') AND scrapy_days = 0 AND user_id!='-';"""
    elif deal_type == 'all' and content_type == 'news':
        sql = """SELECT user_id,scrapy_days,scrapy_nums FROM
                (
                SELECT user_id,scrapy_days,scrapy_nums FROM tb_source_user WHERE source_channel='渠道' AND dept_name='2' AND user_status = 0 AND status_4=0 AND create_time = DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d') AND user_id!='-'
                UNION ALL
                SELECT user_id,scrapy_days,scrapy_nums FROM tb_source_user WHERE source_channel='渠道' AND dept_name='2' AND user_status = 0 AND status_4=0 AND create_time < DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d') AND scrapy_days > 0 AND user_id!='-'
                ) a;"""

    else:
        raise ValueError
    accounts = DataBase().queryall(sql)
    logger.info(f"账户数量：{len(accounts)}")
    return accounts


def set_account_init(deal_type='all', content_type='minivideo'):
    logger.info(f"[{content_type}] [{deal_type}] 账户初始化")
    if deal_type == 'add' and content_type == 'minivideo':
        sql = '''update tb_source_user set status_3 = 0 where source_channel='渠道' AND user_status=0 AND dept_name='2' AND create_time < DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d') AND scrapy_days = 0;'''
    elif deal_type == 'all' and content_type == 'minivideo':
        sql = '''update tb_source_user set status_3 = 0 where source_channel='渠道' AND user_status=0 AND dept_name='2' AND (create_time = DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d')OR(create_time < DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d') AND scrapy_days > 0));'''
    elif deal_type == 'add' and content_type == 'video':
        sql = '''update tb_source_user set status_2 = 0 where source_channel='渠道' AND user_status=0 AND dept_name='2' AND create_time < DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d') AND scrapy_days = 0;'''
    elif deal_type == 'all' and content_type == 'video':
        sql = '''update tb_source_user set status_2 = 0 where source_channel='渠道' AND user_status=0 AND dept_name='2' AND (create_time = DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d')OR(create_time < DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d') AND scrapy_days > 0));'''
    elif deal_type == 'add' and content_type == 'article':
        sql = '''update tb_source_user set status_1 = 0 where source_channel='渠道' AND user_status=0 AND dept_name='2' AND create_time < DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d') AND scrapy_days = 0;'''
    elif deal_type == 'all' and content_type == 'article':
        sql = '''update tb_source_user set status_1 = 0 where source_channel='渠道' AND user_status=0 AND dept_name='2' AND (create_time = DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d')OR(create_time < DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d') AND scrapy_days > 0));'''
    elif deal_type == 'add' and content_type == 'news':
        sql = '''update tb_source_user set status_4 = 0 where source_channel='渠道' AND user_status=0 AND dept_name='2' AND create_time < DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d') AND scrapy_days = 0;'''
    elif deal_type == 'all' and content_type == 'news':
        sql = '''update tb_source_user set status_4 = 0 where source_channel='渠道' AND user_status=0 AND dept_name='2' AND (create_time = DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d')OR(create_time < DATE_FORMAT(SUBDATE(CURDATE(), INTERVAL 1 DAY),'%Y-%m-%d') AND scrapy_days > 0));'''
    else:
        raise ValueError
    status = DataBase().execute(sql)
    logger.info(f"账户初始化数量：{status}")
    return status