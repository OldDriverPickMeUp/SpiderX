#coding=utf-8
"""
新的scanner模块
Scanner主要来整体调度，主要是扫描已插入的代码块
然后更新TaskStore
TaskStore会去调用TaskInfo对象来更新代码块
TaskInfo会托管代码块的变化，当代码块产生变化时会重新加载，并且构建
TaskStore在更新时，会同时检查代码块和配置的变化
当有产生变化的部分时，会更新调度器的任务信息
删除任务应当由Scanner来保证，
Scanner必须能检测有代码块被拔出并执行删除操作
"""
import os,importlib,sys
from . import task
from .corelogger import CoreLogger,DBLogger
from .error import CoreError
from .model import BaseModel
from .config import GlobalConfig
from .parsecmd import StartCommend
from .const import TASK_DIR
from .scheduler import TaskScheduler
from dao.daofactory import DaoFactory
import orm

if os.path.abspath(os.path.sep.join([os.getcwd(), 'core'])) != os.path.dirname(os.path.abspath(__file__)):
    raise Exception('you should start from this project\'s root folder')

ALL_BASE_TASK = [obj for obj in vars(task).values() if hasattr(obj, '__base__') and issubclass(obj,task.UpdateTask)]
MODEL_CLASS = [BaseModel,orm.Model]


def get_m_time_r(path):
    allow_post_fix = '.py'
    if os.path.isdir(path):
        return max([get_m_time_r(os.path.join(path,each_path)) for each_path in os.listdir(path) if each_path.endswith(allow_post_fix)])
    else:
        return os.path.getmtime(path)



class TaskInfo:
    """
    封装动态插拔的代码
    通过文件夹修改时间来做版本控制
    """
    def __init__(self,up_time,import_pkg_name,pkg_dir):
        self.import_pkg_name = import_pkg_name
        self.task_name = os.path.split(pkg_dir)[1]
        self.pkg_dir = pkg_dir
        # 通过pkg_dir 找到所有要递归重新载入的模块名和文件名
        self.last_mod = up_time
        self.task_class_name = None
        self.module = None
        self.all_modules = TaskInfo.get_import_pkgs_r(pkg_dir,import_pkg_name)

    def reload(self):
        last_mod = get_m_time_r(self.pkg_dir)
        if last_mod>self.last_mod:
            self.module,self.task_class_name = self.build(self.task_name,self.import_pkg_name,True)
            self.last_mod=last_mod

    def load(self):
        self.module,self.task_class_name = self.build(self.task_name,self.import_pkg_name)

    @staticmethod
    def get_import_pkgs_r(file_path, module_name):
        if os.path.isdir(file_path):
            can_import_paths = [each for each in os.listdir(file_path) if not each.startswith('__') and each.endswith('.py')]
            final_list=[]
            for each_path in can_import_paths:
                each_file_path = os.path.join(file_path,each_path)
                each_module_name = '.'.join([module_name,each_path.replace('.py', '')])
                r_final_list = TaskInfo.get_import_pkgs_r(each_file_path,each_module_name)
                if isinstance(r_final_list,list):
                    final_list.extend(r_final_list)
                else:
                    final_list.append(r_final_list)
            return final_list

        else:
            return module_name

    def build(self,name,pkg_module_name,reload_flag=False):
        # 当reload_flag 为 True 时，全部模块重新reload
        if reload_flag:
            for each_module in self.all_modules:
                tmp_module_obj = sys.modules.get(each_module)
                if tmp_module_obj is None:
                    importlib.import_module(each_module)
                else:
                    reload(tmp_module_obj)
        else:
            for each_module in self.all_modules:
                tmp_module_obj = sys.modules.get(each_module)
                if tmp_module_obj is None:
                    importlib.import_module(each_module)

        # 找到所有表对象，创建数据库连接
        mainpy_name = '.'.join([pkg_module_name,'main'])
        mainpy = sys.modules.get(mainpy_name)
        if mainpy is None:
            raise CoreError('pkg %s dont have sub module main' % pkg_module_name)
        task_class = None
        task_class_name = None
        for obj_name, obj in vars(mainpy).items():
            if obj_name.startswith('_'):
                continue
            if hasattr(obj,'__base__') and obj not in ALL_BASE_TASK and issubclass(obj,task.UpdateTask):
                CoreLogger.log(message='|---> find task class %s in module %s' % (obj_name,mainpy.__name__),
                               task='scanning')
                task_class = obj
                task_class_name = obj_name
                break

        if task_class is None:
            raise CoreError('did not find a task_class in module %s' % mainpy.__name__)
        task_class.name = name
        author = getattr(task_class,'author',None)
        desc = getattr(task_class,'description',None)
        website = getattr(task_class,'website',None)
        DBLogger.set(name,author,desc,website)


        base_conn = GlobalConfig.instance().get_spider(name)[1]
        if base_conn is None:
            raise CoreError('task %s must have a base_conn' % name)
        if not DaoFactory.have_conn(base_conn):
            raise CoreError('donot have conn %s' % base_conn)
        modelpy_name = '.'.join([pkg_module_name,'model'])
        modelpy = sys.modules.get(modelpy_name)
        if modelpy:
            for obj_name, obj in vars(modelpy).items():
                if hasattr(obj, '__base__') and obj.__base__ in MODEL_CLASS:
                    if obj._conn_name is None:
                        obj._conn_name = base_conn
                    else:
                        if not DaoFactory.have_conn(obj._conn_name):
                            raise CoreError('donot have conn %s' % obj._conn_name)
                    CoreLogger.log('scanning', '    |---> link model %s to %s' % (obj_name,obj._conn_name))
        else:
            CoreLogger.warning('scanner', 'task %s don\'t have a model sub pkg' % name)
        return mainpy, task_class_name


class TaskStore:
    """
    所有任务信息的存储
    还是通过上次修改来判断版本更新
    需要注意的是要在内存中动态创建新的类来加入调度器，
    以防止动态载入模块的代码变化影响到线程内的代码
    真是应该搞master slave模式，这样非常蛋疼
    不易扩展
    """
    module_data = {}
    existing_job= {}
    config_last_mod = {}
    task_info_last_mod = {}

    @staticmethod
    def update_pkg(pkg_dir):
        task_name = os.path.split(pkg_dir)[1]
        if not GlobalConfig.instance().has_spider(task_name):
            return
        task_info = TaskStore.module_data.get(task_name)
        if task_info is None:
            mod_time = get_m_time_r(pkg_dir)
            import_name = '.'.join([TASK_DIR,task_name])
            task_info = TaskInfo(mod_time,import_name,pkg_dir)
            task_info.load()
            TaskStore.module_data[task_name] = task_info
        else:
            task_info.reload()
        TaskStore.update(task_name)


    @staticmethod
    def delete_pkg(pkg_dir):
        task_name = os.path.split(pkg_dir)[1]
        TaskStore.delete(task_name)

    @staticmethod
    def delete(task_name):
        # 先注销掉任务
        # 然后删除module info 还是不要删了，如果在运行中就麻烦了
        job = TaskStore.existing_job.get(task_name)
        if hasattr(job, 'remove'):
            job.remove()
            del TaskStore.existing_job[task_name]
            del TaskStore.config_last_mod[task_name]
            CoreLogger.log('scanning','|---> task %s deleted' % task_name)
        else:
            CoreLogger.fatal('scanning','unexcept job obj for task %s, type %s detail %s' % (task_name,type(job),job))
            if task_name in TaskStore.existing_job.keys():
                del TaskStore.existing_job[task_name]
            if task_name in TaskStore.config_last_mod.keys():
                del TaskStore.config_last_mod[task_name]

    @staticmethod
    def update(task_name):
        """
        更新任务的调度
        """
        job = TaskStore.existing_job.get(task_name)
        if job is None:
            # 直接更新
            last_mod, _, job_type, sche_data = GlobalConfig.instance().get_spider(task_name)
            scheduler = TaskScheduler.scheduler()
            task_info = TaskStore.module_data[task_name]
            task_class_obj = getattr(task_info.module, task_info.task_class_name)
            new_task_class_obj = type(task_class_obj.__name__+'_copy', (task_class_obj,),{})
            job = scheduler.add_job(new_task_class_obj.run, job_type, **sche_data)
            TaskStore.existing_job[task_name] = job
            TaskStore.config_last_mod[task_name] = last_mod
            TaskStore.task_info_last_mod[task_name] = task_info.last_mod
            CoreLogger.log('scanning', '|---> task %s add:%s' % (task_name, sche_data))
        else:
            # 判断版本并更新配置
            task_info = TaskStore.module_data[task_name]
            task_code_last_mod = TaskStore.task_info_last_mod.get(task_name)
            last_mod, _, job_type, sche_data = GlobalConfig.instance().get_spider(task_name)
            if task_code_last_mod is None or task_code_last_mod < task_info.last_mod:
                # 更新代码
                task_class_obj = getattr(task_info.module, task_info.task_class_name)
                new_task_class_obj = type(task_class_obj.__name__ + '_copy', (task_class_obj,),{})
                if last_mod > TaskStore.config_last_mod[task_name]:
                    job.modify(func=new_task_class_obj.run, trigger=TaskScheduler.trigger(job_type,**sche_data))
                    CoreLogger.log('scanning', '|---> task %s updated code and trigger:%s' % (task_name, sche_data))
                    TaskStore.config_last_mod[task_name] = last_mod
                else:
                    job.modify(func=new_task_class_obj.run)
                    CoreLogger.log('scanning', '|---> task %s updated code' % task_name)
                TaskStore.task_info_last_mod[task_name]=task_info.last_mod
            else:
                # 不更新代码
                if last_mod > TaskStore.config_last_mod[task_name]:
                    job.modify(trigger=TaskScheduler.trigger(job_type,**sche_data))
                    CoreLogger.log('scanning', '|---> task %s updated trigger:%s' % (task_name, sche_data))
                    TaskStore.config_last_mod[task_name] = last_mod

class Scanner:
    """
    scanner应该检查代码和配置的变动来对TaskStore进行删改
    """
    __path = os.path.sep.join([os.getcwd(), TASK_DIR])
    _inserted = []
    # Scanner 必须保证只在一个线程运行，首次启动时有主线程调用
    # 动态加载中有daemon task来调用
    # 不给用户用的不加锁
    # 不需要用新式类
    # scanner调用先探测有那些插入模块，然后再检查它们的配置
    # scanner将检查插入代码的上次修改日期，来判断是否要reload模块
    # 当产生load事件后，要自动build
    # build后将模块保存至_scan_modules
    @staticmethod
    def detect():
        tmp_inserted = []
        for each_path in os.listdir(Scanner.__path):
            if each_path.startswith('_') or each_path.startswith('.'):
                continue
            full_path = os.path.join(Scanner.__path, each_path)
            if os.path.isdir(full_path):
                TaskStore.update_pkg(full_path)
                tmp_inserted.append(full_path)
        inserted_set = set(Scanner._inserted)
        tmp_inserted_set = set(tmp_inserted)
        to_delete = inserted_set-tmp_inserted_set
        for n in to_delete:
            TaskStore.delete_pkg(n)
        Scanner._inserted=tmp_inserted

    @staticmethod
    def scan(hot_renew=False):
        CoreLogger.log(task='starting', message='in product mode')
        CoreLogger.log(task='scanning', message='start scan tasks')
        Scanner.detect()
        if hot_renew:
            def daemon_task():
                try:
                    Scanner.detect()
                except Exception as e:
                    CoreLogger.error('daemon',error=e)
            TaskScheduler.scheduler().add_job(daemon_task,'interval',seconds=20)



