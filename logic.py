# -*- coding: utf-8 -*-
#########################################################
# python
import os
import sys
import traceback
import logging
import threading
import subprocess
import platform
import shutil
# third-party

# sjva 공용
from framework import app, path_app_root, db
from framework.logger import get_logger
from framework.util import Util

# 패키지
from .plugin import package_name, logger
from .model import ModelSetting

#########################################################
import requests
import urllib
import time
import threading
from datetime import datetime

class Logic(object):
    db_default = {
        'auto_start' : 'False',
        'port' : '8080',
        'ddns' : 'http://localhost'
    }

    current_process = None

    @staticmethod
    def db_init():
        try:
            for key, value in Logic.db_default.items():
                if db.session.query(ModelSetting).filter_by(key=key).count() == 0:
                    db.session.add(ModelSetting(key, value))
            db.session.commit()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def plugin_load():
        try:
            if platform.system() != 'Windows':
                custom = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin')    
                os.system("chmod 777 -R %s" % custom)

            logger.debug('%s plugin_load', package_name)
            # DB 초기화 
            Logic.db_init()

            # 편의를 위해 json 파일 생성
            from plugin import plugin_info
            Util.save_from_dict_to_json(plugin_info, os.path.join(os.path.dirname(__file__), 'info.json'))

            # 자동시작 옵션이 있으면 보통 여기서 
            if ModelSetting.query.filter_by(key='auto_start').first().value == 'True':
                Logic.scheduler_start()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def plugin_unload():
        try:
            Logic.kill()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def scheduler_start():
        try:
            Logic.run()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def scheduler_stop():
        try:
            Logic.kill()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def setting_save(req):
        try:
            for key, value in req.form.items():
                logger.debug('Key:%s Value:%s', key, value)
                entity = db.session.query(ModelSetting).filter_by(key=key).with_for_update().first()
                entity.value = value
            db.session.commit()
            return True                  
        except Exception as e: 
            logger.error('Exception:%s %s', key)
            logger.error(traceback.format_exc())
            return False


    @staticmethod
    def get_setting_value(key):
        try:
            return db.session.query(ModelSetting).filter_by(key=key).first().value
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def scheduler_function():
        try:
            pass
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
    

    # 기본 구조 End
    ##################################################################

    @staticmethod
    def run():
        if Logic.current_process is None:
            target = os.path.join(os.path.dirname(__file__), 'torrssen2', 'docker')
            for f in os.listdir(target):
                if f.endswith('.jar'):
                    target = os.path.join(target, f)
                    break
            port = ModelSetting.get('port') 
            if port == '8080':
                cmd = ['java', '-jar', '-Dfile.encoding=UTF-8', target]
            else:
                cmd = ['java', '-jar', '-Dfile.encoding=UTF-8', '-Dserver.port=%s' % port, target]

            Logic.current_process = subprocess.Popen(cmd)
            #--session_dir="your/new/shorter/path"

    @staticmethod
    def kill():
        try:
            if Logic.current_process is not None and Logic.current_process.poll() is None:
                import psutil
                process = psutil.Process(Logic.current_process.pid)
                for proc in process.children(recursive=True):
                    proc.kill()
                process.kill()
            Logic.current_process = None
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def install():
        try:
            def func():
                import system
                current_path = os.path.dirname(__file__)
                target = os.path.join(current_path, 'torrssen2')
                Logic.kill()
                if Logic.is_installed():
                    if platform.system() == 'Windows':
                        os.system('rmdir /S /Q "{}"'.format(target))
                    else:
                        shutil.rmtree(target)
                commands = [
                    ['msg', u'잠시만 기다려주세요.'],
                    ['git', 'clone', 'https://github.com/tarpha/torrssen2', target, '--depth', '1'],
                ]
                if app.config['config']['running_type'] == 'docker':
                    commands.append(['apk', 'add', 'openjdk8-jre'])
                else:
                    commands.append(['msg', u'openjdk8 JRE가 설치되어 있고, java 명령을 실행할 수 있어야합니다. 실행이 안되는 경우 설치여부를 확인하세요'])
                commands.append(['msg', u'설치가 완료되었습니다.'])
                system.SystemLogicCommand.start('설치', commands)
            t = threading.Thread(target=func, args=())
            t.setDaemon(True)
            t.start()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def is_installed():
        try:
            import system
            current_path = os.path.dirname(__file__)
            target = os.path.join(current_path, 'torrssen2')
            if os.path.exists(target) and os.path.isdir(target):
                return True
            else:
                return False
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
