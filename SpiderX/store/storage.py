#coding=utf-8


class ModelStorage:
    def __init__(self,model=None,unique=None,update=False):
        self.model = model
        if not isinstance(unique, list):
            unique = [unique]
        self.unique = unique
        self.update=update
        self.log_method = None

    def set_log_method(self,func):
        self.log_method = func
        return self

    def push(self,data):
        if not isinstance(data,list):
            data=[data]

        if self.unique:
            # 有unique参数先查找unique
            count=0
            for each_data in data:
                filter_data = {each_key:each_data[each_key] for each_key in self.unique}
                existing_obj = self.model.all_objects().filter(**filter_data).select()
                if existing_obj is not None:
                    if self.update:
                        existing_obj.update_datamap(each_data)
                        existing_obj.save()
                    continue
                new_obj = self.model()
                new_obj.update_datamap(each_data)
                new_obj.save()
                count+=1
                if callable(self.log_method):
                    self.log_method(each_data)
            return count
        else:
            for each_data in data:
                new_obj = self.model()
                new_obj.update_datamap(each_data)
                new_obj.save()
                if callable(self.log_method):
                    self.log_method(each_data)
            return len(data)