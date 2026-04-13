""""所有工具函数定义，统一返回str格式"""
from datetime import datetime

def get_current_time()->str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_tools():
    return [
        {
            "type":"function",
            "function":{
                "name":"get_current_time",
                "description":"获取当前日期和时间",
                "parameters":{
                    "type":"object",
                    "properties":{},
                    "required":[]
                }
            }
        }
    ]

TOOL_FUNCTIONS = {
    "get_current_time": get_current_time,
}